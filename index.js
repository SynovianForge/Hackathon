export default (app) => {
  app.log.info("The Bouncer is online with Diagnostics!");

  const PYTHON_API_URL = process.env.PYTHON_API_URL || "http://localhost:8000";
  const FRONTEND_URL = process.env.FRONTEND_URL || "http://localhost:3000/quiz";
  const GITHUB_PAT = process.env.GITHUB_PAT;

  app.on(["pull_request.opened", "pull_request.synchronize", "pull_request.reopened"], async (context) => {
    try {
      const prNumber = context.payload.pull_request.number;
      const owner = context.payload.repository.owner.login;
      const repo = context.payload.repository.name;
      const sha = context.payload.pull_request.head.sha;
      const user_id = context.payload.pull_request.user.login;

      app.log.info(`Checking PR #${prNumber} | Commit: ${sha}`);

      // 1. Get the PR diff from GitHub
      const filesResponse = await context.octokit.rest.pulls.listFiles({
        owner, repo, pull_number: prNumber
      });

      const files = filesResponse.data.map(f => ({
        filename: f.filename,
        diff: f.patch || '',
        context: ''
      }));

      const total_diff_size = filesResponse.data.reduce(
        (sum, f) => sum + f.additions + f.deletions, 0
      );

      // 2. Ask the Python Brain — same endpoint the VS Code extension uses
      const response = await fetch(`${PYTHON_API_URL}/api/check-push`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id, commit_hash: sha, total_diff_size, files })
      });

      if (!response.ok) {
        app.log.error(`🚨 Python API error: ${response.status}`);
        return;
      }

      const data = await response.json();

      // 3. React to whatever the Brain says — PASS comes from any early exit
      if (data.action === 'PASS') {
        await context.octokit.rest.repos.createCommitStatus({
          owner, repo, sha, state: "success",
          context: "Gatekeeper Verification",
          description: data.message || "Verified."
        });
        app.log.info(`✅ Commit ${sha} passed. Reason: ${data.reason}`);
      } else {
        await context.octokit.rest.repos.createCommitStatus({
          owner, repo, sha, state: "pending",
          context: "Gatekeeper Verification",
          description: "Awaiting quiz verification..."
        });

        const magicLink = `${FRONTEND_URL}?quiz_id=${data.quiz_id}&commit=${sha}`;
        const commentBody = `### 🛑 Gatekeeper Check Required\n\nYou bypassed the IDE extension.\n\n👉 **[Verify Commit](${magicLink})**`;

        try {
          await context.octokit.rest.issues.createComment(context.issue({ body: commentBody }));
        } catch (commentErr) {
          if (commentErr.status === 403 && GITHUB_PAT) {
            app.log.warn(`⚠️ Installation token blocked (403). Falling back to PAT.`);
            const patRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/issues/${prNumber}/comments`, {
              method: 'POST',
              headers: { 'Authorization': `token ${GITHUB_PAT}`, 'Content-Type': 'application/json', 'Accept': 'application/vnd.github+json' },
              body: JSON.stringify({ body: commentBody })
            });
            if (!patRes.ok) {
              const errText = await patRes.text();
              throw new Error(`PAT comment fallback failed: ${patRes.status} ${errText}`);
            }
          } else {
            throw commentErr;
          }
        }
        app.log.info(`🛑 Commit ${sha} pending. Magic link dropped.`);

        // Poll the DB until the quiz is answered or we time out (5 minutes)
        const pollInterval = 5000;
        const maxAttempts = 60;
        let attempts = 0;

        const poll = async () => {
          if (attempts >= maxAttempts) {
            await context.octokit.rest.repos.createCommitStatus({
              owner, repo, sha, state: "failure",
              context: "Gatekeeper Verification",
              description: "Quiz timed out — not answered within 5 minutes."
            });
            app.log.warn(`⏰ Quiz ${data.quiz_id} timed out.`);
            return;
          }

          attempts++;
          try {
            const quizRes = await fetch(`${PYTHON_API_URL}/api/quiz/${data.quiz_id}`);
            const quiz = await quizRes.json();

            if (quiz.status === 'PASS') {
              await context.octokit.rest.repos.createCommitStatus({
                owner, repo, sha, state: "success",
                context: "Gatekeeper Verification",
                description: "Quiz passed. Commit verified."
              });
              app.log.info(`✅ Quiz ${data.quiz_id} passed. Commit ${sha} unlocked.`);
            } else if (quiz.status === 'FAIL') {
              await context.octokit.rest.repos.createCommitStatus({
                owner, repo, sha, state: "failure",
                context: "Gatekeeper Verification",
                description: "Quiz failed. Commit blocked."
              });
              app.log.info(`❌ Quiz ${data.quiz_id} failed. Commit ${sha} blocked.`);
            } else {
              setTimeout(poll, pollInterval);
            }
          } catch (pollErr) {
            app.log.error(`Poll error: ${pollErr.message}`);
            setTimeout(poll, pollInterval);
          }
        };

        setTimeout(poll, pollInterval);
      }
    } catch (err) {
      app.log.error(`🚨 CRASH LOG: ${err.message}`);
    }
  });
};
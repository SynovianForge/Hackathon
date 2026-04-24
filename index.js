export default (app) => {
  app.log.info("The Bouncer is online with Diagnostics!");

  // Ensure these are set in the GitHub App's environment variables
  const PYTHON_API_URL = process.env.PYTHON_API_URL || "http://localhost:8000"; 
  const FRONTEND_URL = process.env.FRONTEND_URL || "http://localhost:3000/quiz"; 

  app.on(["pull_request.opened", "pull_request.synchronize", "pull_request.reopened"], async (context) => {
    try {
      const prNumber = context.payload.pull_request.number;
      const owner = context.payload.repository.owner.login;
      const repo = context.payload.repository.name;
      const sha = context.payload.pull_request.head.sha;

      app.log.info(`Checking PR #${prNumber} | Commit: ${sha}`);

      // 1. The Single Source of Truth (Ask the Python Brain)
      let isVerified = false;
      try {
        const response = await fetch(`${PYTHON_API_URL}/api/check-commit?sha=${sha}`);
        if (response.ok) {
          const data = await response.json();
          isVerified = (data.status === 'verified');
        } else {
          app.log.warn(`⚠️ Python API returned status: ${response.status}`);
        }
      } catch (fetchError) {
         app.log.error(`🚨 Python API Unreachable: ${fetchError.message}`);
         // If the backend is down, we default to locking the PR (fail-secure)
      }

      // 2. Logic Execution (Lock or Unlock)
      if (isVerified) {
        await context.octokit.rest.repos.createCommitStatus({
          owner, repo, sha, state: "success",
          context: "Gatekeeper Verification",
          description: "Verified via IDE."
        });
        app.log.info(`✅ Commit ${sha} unlocked.`);
      } else {
        await context.octokit.rest.repos.createCommitStatus({
          owner, repo, sha, state: "pending",
          context: "Gatekeeper Verification",
          description: "Awaiting quiz verification..."
        });

        const magicLink = `${FRONTEND_URL}?commit=${sha}`;
        const commentBody = `### 🛑 Gatekeeper Check Required\n\nYou bypassed the IDE extension.\n\n👉 **[Verify Commit](${magicLink})**`;

        await context.octokit.rest.issues.createComment(context.issue({ body: commentBody }));
        app.log.info(`🛑 Commit ${sha} pending. Magic link dropped.`);
        
        // 3. Register the pending status with the Python Brain
        try {
            await fetch(`${PYTHON_API_URL}/api/register-commit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sha: sha, status: 'pending' })
            });
        } catch (err) {
            app.log.error(`🚨 Failed to sync pending status to Python Brain: ${err.message}`);
        }
      }
    } catch (err) {
      app.log.error(`🚨 CRASH LOG: ${err.message}`);
    }
  });
};
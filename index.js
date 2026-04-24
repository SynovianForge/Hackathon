import { createClient } from '@supabase/supabase-js';

export default (app) => {
  app.log.info("The Bouncer is online with Diagnostics!");

  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    app.log.error("🚨 Missing Supabase credentials in .env!");
  }

  const supabase = createClient(supabaseUrl, supabaseKey);
  const FRONTEND_URL = "http://localhost:3000/quiz"; 

  app.on(["pull_request.opened", "pull_request.synchronize", "pull_request.reopened"], async (context) => {
    try {
      const prNumber = context.payload.pull_request.number;
      const owner = context.payload.repository.owner.login;
      const repo = context.payload.repository.name;
      const sha = context.payload.pull_request.head.sha;

      app.log.info(`Checking PR #${prNumber} | Commit: ${sha}`);

      // 1. Supabase Check
      const { data, error } = await supabase
        .from('commit_verifications')
        .select('status')
        .eq('commit_sha', sha)
        .single();

      if (error && error.code !== 'PGRST116') { 
         app.log.error(`🚨 Supabase Error: ${error.message}`);
      }

      // 2. Logic Execution (Fixed Octokit syntax for v14+)
      if (data && data.status === 'verified') {
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

        // Fixed issues syntax
        await context.octokit.rest.issues.createComment(context.issue({ body: commentBody }));
        app.log.info(`🛑 Commit ${sha} pending. Magic link dropped.`);
        
        await supabase.from('commit_verifications').upsert({ commit_sha: sha, status: 'pending' });
      }
    } catch (err) {
      app.log.error(`🚨 CRASH LOG: ${err.message}`);
    }
  });
};
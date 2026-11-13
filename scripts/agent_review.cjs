/** Decide whether this PR event may start a review with write access. */
module.exports = function shouldReview({ eventName, payload }) {
  const pr = payload.pull_request;
  if (eventName !== "pull_request" || !pr || pr.draft) return false;
  if (!["opened", "synchronize", "ready_for_review", "reopened"].includes(payload.action)) return false;
  if (!pr.head.repo || pr.head.repo.full_name !== payload.repository.full_name) return false;
  if (pr.head.ref === payload.repository.default_branch) return false;
  // Only skip the reviewer's pushes, not PRs authored by Claude elsewhere.
  return !(payload.action === "synchronize" && payload.sender.login === "claude[bot]");
};

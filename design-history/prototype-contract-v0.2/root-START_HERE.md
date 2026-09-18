# Start here

The current deliverable is a runnable local prototype, with the corrected three-panel UX. The larger autonomous QA framework remains a future reference.

1. Run the four setup/start commands in README.md and open localhost:8000.
2. Choose a synthetic example, select the separate flag, and review. Copy the standard comments. Try thumbs-down with only a reason.
3. Change only the flag: old results become stale. Restore reviewed input or request another review.
4. Read prototype/IMPLEMENTATION_STATUS.md and inspect prototype/assets/implementation-desktop.png. This screenshot shows the actual implementation.
5. Review prototype/BLUEPRINT.html for the consolidated design, API, roadmap and validation record.

## Next bounded work

Review the actual UX with QA participants, then configure a real model for synthetic evaluation. Add the Vesta manual and critical vocabulary when available, agree expected observations with a domain reviewer, and run the included seed cases through the evaluation harness. Measure correctness and radiologist attention cost separately from software execution success. The harness exports results for human review; it does not assign clinical pass/fail automatically.

Only after the prototype findings should the detailed MVP blueprint, roadmap and implementation plan be developed. Do not add fleet operations, integrations or evidence UI simply because they appear in the earlier framework.

## Sources of truth

Current user instructions → prototype/BLUEPRINT.md → prototype/UX_DESIGN_SYSTEM.md and API_DESIGN.md → actual implementation/status. Broader framework documents apply only where consistent with the narrower prototype.

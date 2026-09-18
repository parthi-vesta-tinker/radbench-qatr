export const feedbackReasons: Record<string, string> = {
  missed_observation: 'Missed observation',
  unnecessary_observation: 'Unnecessary observation',
  incorrect_observation: 'Incorrect observation',
  wrong_grouping: 'Wrong grouping',
  unclear_wording: 'Unclear wording',
  other: 'Other',
};
export const reasonLabel = (reason: string) => feedbackReasons[reason] ?? reason.replaceAll('_', ' ');

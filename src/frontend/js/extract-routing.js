export function buildExtractRouting(plaza, discussion) {
  const participants = Array.isArray(plaza?.participants) ? plaza.participants : [];
  const teamIds = [...new Set(participants.map((participant) => participant.team_id).filter(Boolean))];
  const moderatorAgentId = String(
    discussion?.moderator_agent_id ||
    discussion?.moderator?.agent_id ||
    ''
  ).trim();

  let preferredTeamId = '';
  if (moderatorAgentId) {
    const moderatorParticipant = participants.find((participant) => participant.agent_id === moderatorAgentId && participant.team_id);
    if (moderatorParticipant) preferredTeamId = moderatorParticipant.team_id;
  }
  if (!preferredTeamId) {
    const chairParticipant = participants.find((participant) => participant.niche_role === 'moderator' && participant.team_id);
    if (chairParticipant) preferredTeamId = chairParticipant.team_id;
  }
  if (!preferredTeamId && teamIds.length) preferredTeamId = teamIds[0];

  return { teamIds, preferredTeamId };
}

export function prioritizeExtractTeams(teams, participantTeamIds, preferredTeamId) {
  const items = Array.isArray(teams) ? teams.slice() : [];
  const allowedIds = Array.isArray(participantTeamIds) && participantTeamIds.length
    ? new Set(participantTeamIds.filter(Boolean))
    : null;
  const displayTeams = allowedIds
    ? items.filter((team) => allowedIds.has(team.team_id))
    : items;

  if (!preferredTeamId) return displayTeams;
  const preferredIndex = displayTeams.findIndex((team) => team.team_id === preferredTeamId);
  if (preferredIndex > 0) {
    const [preferredTeam] = displayTeams.splice(preferredIndex, 1);
    displayTeams.unshift(preferredTeam);
  }
  return displayTeams;
}

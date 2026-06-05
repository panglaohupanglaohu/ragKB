export function buildExtractRouting(plaza, discussion) {
  const participants = Array.isArray(plaza?.participants) ? plaza.participants : [];
  const teamIds = [...new Set(participants.map((participant) => participant.team_id).filter(Boolean))];
  const moderatorAgentId = String(
    discussion?.moderator_agent_id ||
    discussion?.moderator?.agent_id ||
    ''
  ).trim();

  let preferredTeamId = '';
  // 优先级 1: 讨论的议事长所属团队
  if (moderatorAgentId) {
    const moderatorParticipant = participants.find((participant) => participant.agent_id === moderatorAgentId && participant.team_id);
    if (moderatorParticipant) preferredTeamId = moderatorParticipant.team_id;
  }
  // 优先级 2: 广场中 role='moderator' 的参与者团队
  if (!preferredTeamId) {
    const chairParticipant = participants.find((participant) => participant.niche_role === 'moderator' && participant.team_id);
    if (chairParticipant) preferredTeamId = chairParticipant.team_id;
  }
  // 优先级 3: plaza 自身的 team_id（如果后端支持）
  if (!preferredTeamId && plaza?.team_id) {
    preferredTeamId = plaza.team_id;
  }
  // 优先级 4: 参与者团队中的第一个
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

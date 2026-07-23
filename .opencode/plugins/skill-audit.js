export const SkillAudit = async ({ client }) => {
  // 用于确认插件已经成功加载
  await client.app.log({
    body: {
      service: "skill-audit",
      level: "info",
      message: "Skill audit plugin initialized",
    },
  })

  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "skill") return

      const skillName =
        typeof output.args?.name === "string"
          ? output.args.name
          : "(unknown)"

      await client.app.log({
        body: {
          service: "skill-audit",
          level: "info",
          message: `Loading skill: ${skillName}`,
          extra: {
            skill: skillName,
          },
        },
      })
    },
  }
}

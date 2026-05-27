const host = "agent-assurance.dev";
const indexNowVerification = "ab02de421738fed7233351db2d3ab5f4a4fbddb8050cc6c977b2fc940b8c8a68";
const indexNowVerificationLocation = `https://${host}/${indexNowVerification}.txt`;
const endpoint = process.env.INDEXNOW_ENDPOINT || "https://api.indexnow.org/indexnow";

const urlList = [
  `https://${host}/`,
  `https://${host}/index.md`,
  `https://${host}/spec/`,
  `https://${host}/spec/index.md`,
  `https://${host}/profiles/`,
  `https://${host}/profiles/index.md`,
  `https://${host}/validators/`,
  `https://${host}/validators/index.md`,
  `https://${host}/compare/`,
  `https://${host}/compare/index.md`,
  `https://${host}/agent-readiness/`,
  `https://${host}/agent-readiness/index.md`,
  `https://${host}/llms.txt`,
  `https://${host}/sitemap.md`,
  `https://${host}/sitemap.xml`,
  `https://${host}/.well-known/agent.json`,
  `https://${host}/.well-known/agent-skills/index.json`,
  `https://${host}/agent.json`,
  `https://${host}/agent-skills.json`,
];

const response = await fetch(endpoint, {
  method: "POST",
  headers: {
    "content-type": "application/json; charset=utf-8",
  },
  body: JSON.stringify({
    host,
    key: indexNowVerification,
    keyLocation: indexNowVerificationLocation,
    urlList,
  }),
});

const body = await response.text();
console.log(`${endpoint} -> ${response.status} ${response.statusText}`);
if (body.trim()) console.log(body);
if (!response.ok) process.exit(1);

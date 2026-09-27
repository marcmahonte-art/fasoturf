const res = await fetch("http://127.0.0.1:8000/api/dashboard");
if (!res.ok) { console.error("HTTP", res.status); process.exit(1); }
const d = await res.json();

const need = ["targetDate","user","subscription","nextRace","followedRaces","topPredictions",
  "predictionContext","predictionUnavailableReason","performance","performanceUnavailableReason",
  "coverage","notifications","dataStatus","isLive"];
const missing = need.filter(k => !(k in d));
console.log("top-level missing:", missing.length ? missing : "none");

if (d.nextRace) {
  const rn = ["id","meetingNumber","raceNumber","hippodrome","participantCount","distanceMeters",
    "startTime","betType","discipline","imageUrl","status","date","isLonab","origin"];
  console.log("nextRace missing:", rn.filter(k => !(k in d.nextRace)));
  console.log("nextRace.status:", d.nextRace.status, "| startTime:", JSON.stringify(d.nextRace.startTime));
}
if (d.topPredictions.length) {
  const pn = ["horseId","horseName","horseNumber","winProbability","top3Probability","top5Probability",
    "rank","confidence","modelVersion","predictionVersion","raceLabel","raceId","odds","valueEdge","origin"];
  console.log("prediction missing:", pn.filter(k => !(k in d.topPredictions[0])));
  const p = d.topPredictions[0];
  console.log(`top1: #${p.horseNumber} ${p.horseName} win=${p.winProbability} (ratio) -> ${Math.round(p.winProbability*100)}%`);
}
console.log("notifications.configured:", d.notifications.configured);
console.log("subscription:", JSON.stringify(d.subscription));
console.log("performance:", d.performance, "| reason:", (d.performanceUnavailableReason||"").slice(0,50));
console.log("coverage keys:", Object.keys(d.coverage).join(","));
console.log("dataStatus:", JSON.stringify(d.dataStatus));
console.log("context:", d.predictionContext);

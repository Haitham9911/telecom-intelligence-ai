const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const ctx={document:{addEventListener(){}},t:(ar,en)=>en};vm.createContext(ctx);vm.runInContext(fs.readFileSync('oman.js','utf8'),ctx);
ctx.fixture=JSON.parse(execFileSync('python',['-c',"import json,oman_refresh;print(json.dumps(oman_refresh.combined('data')))"],{encoding:'utf8',maxBuffer:8*1024*1024}));vm.runInContext('omanData=fixture',ctx);const calc=s=>vm.runInContext(s,ctx);
assert.equal(calc("omLatest('mobile').value"),6891335);
assert.equal(calc("omLatest('mobile_including_m2m').value"),8606008);
assert.equal(calc("omRecord('mobile','2026-06-30').value"),6619238);
assert.equal(calc("omRecord('population','2026-09-30').value"),5454352);
assert.deepEqual(Array.from(calc('omYears()')),[2021,2022,2023,2024,2025]);
assert.equal(calc("omAnnual('prepaid',2025).value"),5323009); // TRA vintage, not monthly NCSI conflict.
assert.equal(calc("omAnnual('fbb_revenue',2026)"),null); // Incomplete year is not an annual result.
assert.ok(calc("omAnnual('fbb_revenue',2025).value")>0);
assert.equal(calc('Math.round(omEstimate(6619238,16.1,1).value)'),1065697);
assert.equal(calc('Math.round(omEstimate(591630,19,0).value)'),112410);
assert.equal(calc('omEstimate(591630,101,0)'),null);
assert.equal(calc('omEstimate(0,19,0)'),null);
assert.equal(calc("omanData.shares.find(s=>s.id==='mobile-2026-06-30').total"),6619238); // Never the newer September total.
console.log('Oman dates, source vintages, complete-year flows and rounded-share estimates: 13 checks passed');

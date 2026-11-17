const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const ctx={document:{addEventListener(){}},t:(ar,en)=>en};vm.createContext(ctx);
for(const file of ['oman.js','oman-analysis.js'])vm.runInContext(fs.readFileSync(file,'utf8'),ctx);
ctx.fixture=JSON.parse(execFileSync('python',['-c',"import json,oman_refresh;print(json.dumps(oman_refresh.combined('data')))"],{encoding:'utf8',maxBuffer:8*1024*1024}));
const calc=s=>vm.runInContext(s,ctx);calc('omanData=fixture');
assert.equal(calc("oaPreviousMonth('2024-03-31')"),'2024-02-29');
assert.equal(calc("oaPreviousMonth('2026-01-31')"),'2025-12-31');
assert.equal(calc("oaMonthPair('mobile').delta"),95294);
assert.equal(calc("oaMonthPair('prepaid').delta+oaMonthPair('postpaid').delta"),95294);
assert.equal(calc("oaMonthPair('m2m').delta"),-5150);
assert.equal(calc("oaMonthPair('mobile_voice_revenue')"),null); // Quarterly flow is never a month balance.
calc("const pair=oaSharePair('fixed_broadband');const movement=oaShareChange(pair.current,pair.previous,'Awasr')");
assert.ok(Math.abs(calc('movement.delta')-4606.44)<1e-8);
assert.ok(Math.abs(calc('movement.marketEffect+movement.shareEffect-movement.delta'))<1e-8);
assert.equal(calc('movement.pp'),1);
assert.ok(calc('movement.low<0&&movement.high>0')); // Rounding prevents a confident direction for the estimated count.
assert.equal(calc("oaSharePair('mobile')"),null);
assert.equal(calc("oaShareChange(omanData.shares[0],omanData.shares[2],'Vodafone')"),null);
assert.equal(calc("oaYearRows('mobile')[0].growth"),null);
assert.ok(calc("oaYearRows('fbb_revenue')[4].growth")!==null);
const csv=calc('oaCsv()');assert.ok(csv.includes('Q4 monthly ARPU'));assert.ok(csv.includes('sum of four quarters'));
assert.ok(!csv.includes('NaN'));assert.ok(!csv.includes('undefined'));
calc("omanData={...fixture,national:fixture.national.filter(r=>!(r.metric==='fiber'&&r.period_end==='2026-08-31'))}");
assert.equal(calc("oaMonthPair('fiber')"),null); // No July-to-September comparison disguised as MoM.
calc("omanData={...fixture,national:fixture.national.map(r=>r.metric==='fiber'&&r.period_end==='2026-08-31'?{...r,source_id:'another_vintage'}:r)}");
assert.equal(calc("oaMonthPair('fiber')"),null); // Do not create growth from a mismatched publication.
console.log('Oman analysis: 20 checks passed, including source-vintage, period and rounding safeguards');

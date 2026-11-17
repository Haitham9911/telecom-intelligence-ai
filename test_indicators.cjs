const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
// Build the fixture offline from committed sources, including on a clean checkout.
const fixture=execFileSync('python',['-c',"import json,financial_refresh; print(json.dumps(financial_refresh.combined('data')))"],{encoding:'utf8',maxBuffer:8*1024*1024});
const ctx={document:{addEventListener(){}},lang:'en',t:(_,en)=>en};vm.createContext(ctx);vm.runInContext(fs.readFileSync('indicators.js','utf8'),ctx);ctx.testData=JSON.parse(fixture);vm.runInContext('indicatorData=testData',ctx);const calc=x=>vm.runInContext(x,ctx);
assert.deepEqual(Array.from(calc('indYears()')),[2021,2022,2023,2024,2025]);
assert.equal(calc("indRecord('OTEL','customers',2021)"),null);
assert.ok(calc("indRecord('OTEL','domestic_customers',2021).value")>0);
assert.equal(calc("indLatest('TMUS','customers')"),null);
assert.ok(calc("indLatest('TMUS','postpaid_accounts').value")>0);
assert.equal(calc("indRecord('ZAIN','capex_intensity',2025)"),null); // USD capex versus KWD revenue.
assert.equal(calc("indRecord('OTEL','capex_intensity',2025)"),null); // Domestic CapEx is not group CapEx.
assert.equal(calc("indRecord('STC','customers',2025)"),null);
assert.equal(calc("indRecord('VZ','net_debt',2025)"),null); // Do not relabel net unsecured debt.
assert.ok(calc("indRecord('VZ','net_unsecured_debt',2021).value")>0);
assert.ok(calc("indRecord('VZ','current_ratio',2025).value")>0);
assert.equal(calc("indRecord('TEF','debt_to_equity',2025)"),null);
console.log('Indicator scope, currency, missing values and reporting dates: 12 checks passed');

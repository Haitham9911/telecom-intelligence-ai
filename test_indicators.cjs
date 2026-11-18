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
assert.equal(calc("indRecord('DTE','working_capital',2022).value"),-6245);
assert.equal(calc("indRecord('DTE','working_capital',2022).currency"),'EUR');
assert.ok(Math.abs(calc("indRecord('ORDS','working_capital',2025).value")-6845.433)<1e-8);
assert.ok(Math.abs(calc("indRecord('ORDS','current_ratio',2025).value")-21602.134/14756.701)<1e-10);
assert.equal(calc("indRecord('ORDS','current_assets',2021).source_vintage"),'Annual Report 2022');
assert.match(calc("indRecord('ORDS','current_assets',2022).basis_en"),/Note 49/);
assert.match(calc("indRecord('DTE','operating_cash_flow',2021).basis_en"),/EUR 808m.*discontinued/);
for(const company of ['ORDS','DTE'])for(const metric of ['current_assets','current_liabilities','total_liabilities','operating_cash_flow']){
 assert.deepEqual(Array.from(calc(`indicatorData.records.filter(r=>r.company_id==='${company}'&&r.metric==='${metric}'&&r.period_type==='annual').map(r=>r.year).sort()`)),[2021,2022,2023,2024,2025]);
}
// A ratio/subtraction must not combine group and domestic balances or report vintages.
calc("indRaw('ORDS','current_liabilities',2025).scope_en='Domestic only'");
assert.equal(calc("indRecord('ORDS','working_capital',2025)"),null);
assert.equal(calc("indRecord('ORDS','current_ratio',2025)"),null);
calc("indRaw('ORDS','current_liabilities',2025).scope_en='Consolidated group';indRaw('ORDS','current_liabilities',2025).source_vintage='Annual Report 2024'");
assert.equal(calc("indRecord('ORDS','working_capital',2025)"),null);
// Zero current liabilities still permit a subtraction, but not division.
calc("indRaw('ORDS','current_liabilities',2025).source_vintage='Annual Report 2025';indRaw('ORDS','current_liabilities',2025).value=0");
assert.equal(calc("indRecord('ORDS','current_ratio',2025)"),null);
assert.equal(calc("indRecord('ORDS','working_capital',2025).value"),21602.134);
console.log('Indicator scope, currencies, five-year liquidity, provenance and calculation guards passed');

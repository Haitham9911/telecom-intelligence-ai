'use strict';

const omOperatorNames = {
  omantel: ['عمانتل', 'Omantel'], ooredoo: ['أوريدو عُمان', 'Ooredoo Oman'],
  vodafone: ['فودافون عُمان', 'Vodafone Oman'], awasr: ['أواصر', 'Awasr'],
  friendi: ['فرندي', 'FRiENDi'], renna: ['مجان (رنة وريد بُل موبايل)', 'Majan (Renna and Red Bull Mobile)'],
  broadband: ['الشركة العُمانية للنطاق العريض', 'Oman Broadband'], starlink: ['ستارلينك مسقط', 'Starlink Muscat']
};
const omServices = {
  fixed: ['الاتصالات العامة الثابتة', 'Public fixed telecom'], mobile: ['الاتصالات العامة المتنقلة', 'Public mobile telecom'],
  international: ['الاتصالات العامة الدولية', 'International public telecom'], resale: ['إعادة بيع خدمات المتنقل', 'Mobile resale'],
  infrastructure: ['بنية النطاق العريض وخدماته', 'Broadband infrastructure and services'],
  satellite: ['اتصالات ثابتة عبر الأقمار الصناعية', 'Fixed satellite communications']
};
function omRef(id, label) {
  const url = omanData.research.sources[id];
  return url ? external(url, label) : '';
}
function omNum(value, digits = 0) {
  return Number.isFinite(value) ? '<bdi dir="ltr">' + fmt(value, digits) + '</bdi>' : '—';
}
function omTable(headers, rows) {
  const head = headers.map(h => '<th scope="col">' + h + '</th>').join('');
  const body = rows.map(([title, ...cells]) => '<tr><th scope="row">' + title + '</th>' +
    cells.map(cell => '<td>' + cell + '</td>').join('') + '</tr>').join('');
  return '<div class="table-wrap"><table class="research-table"><thead><tr>' + head +
    '</tr></thead><tbody>' + body + '</tbody></table></div>';
}
function omNote(body) {
  return '<p class="footnote">' + body + '</p>';
}
function omCallout(title, body) {
  return '<div class="scope-explainer"><strong>' + title + '</strong><p>' + body + '</p></div>';
}
function omMatchedRate(count, population) {
  return Number.isFinite(count) && population > 0 ? count / population * 100 : null;
}
function omPenetration() {
  const source = t('المصادر', 'Sources'), date = t('نهاية الفترة', 'Period end');
  const records = omanData.research.population;
  const metrics = [
    ['mobile', 'mobile_penetration'], ['mobile_broadband', 'mbb_penetration']
  ];
  let html = '';
  for (const [count, published] of metrics) {
    const rows = records.map(p => {
      const n = omRecord(count, p.period_end), rate = omRecord(published, p.period_end);
      return [p.period_end, omNum(n?.value), omNum(p.value), omNum(rate?.value, 2),
        omNum(omMatchedRate(n?.value, p.value), 2), [omSource(n), omRef(p.source, t('السكان', 'Population'))].join(' · ')];
    });
    html += section(omLabel(count), t('اشتراك لكل 100 نسمة. تُحسب النسبة الموحدة من عدد الاشتراكات والسكان المسجلين في نهاية الفترة نفسها.',
      'Subscriptions per 100 people. The matched rate uses subscriptions and registered residents at the same period end.')) +
      omTable([date, t('الاشتراكات', 'Subscriptions'), t('السكان المسجلون', 'Registered residents'),
        t('نسبة الهيئة المنشورة', 'TRA published rate'), t('المحسوبة للفترة نفسها', 'Matched-period rate'), source], rows);
  }
  html += omCallout(t('كيف نفسّر تغير الانتشار؟', 'Reading the change in penetration'),
    t('في 2022 ارتفع عدد الشرائح، وارتفع عدد السكان بوتيرة أسرع. لذلك انخفضت الحسبة على سكان ديسمبر من 131.80 إلى 126.20 لكل 100 نسمة، بينما ارتفع معدل الهيئة المنشور من 131.40 إلى 137.11. ويمكن للفرد امتلاك عدة شرائح.',
    'In 2022 the SIM count increased, but the resident population grew faster. Using December population, subscriptions per 100 fell from 131.80 to 126.20, while the published TRA rate rose from 131.40 to 137.11. A person can hold multiple SIMs.') +
    ' ' + omRef('traMobile', 'TRA') + ' · ' + omRef('ncsiPopulation', 'NCSI'));
  const fixedRows = records.map(p => {
    const metrics = ['fixed_broadband','fbb_household_penetration','fixed_voice','voice_household_penetration'];
    const values = metrics.map(k => omRecord(k,p.period_end));
    return [p.period_end, ...values.map((v,i) => omNum(v?.value, i % 2 ? 2 : 0)), omSource(values[0])];
  });
  html += section(t('انتشار الخدمات الثابتة', 'Fixed-service penetration'), t('تستخدم الهيئة عدد الأسر مقامًا. وقد يشمل البسط اشتراكات تجارية وسكنية.',
    'TRA uses households as the denominator. Subscription totals can include business and residential connections.')) +
    omTable([date, omLabel('fixed_broadband'), t('لكل 100 أسرة', 'Per 100 households'), omLabel('fixed_voice'),
      t('لكل 100 أسرة', 'Per 100 households'), source], fixedRows) +
    omNote(t('استخدم تقرير النصف الأول من 2026 مرجعًا قدره 725,967 أسرة. تعني الشرطة أن المصدر المعروض لم ينشر معدلًا لتلك الفترة.',
      'The H1 2026 report used 725,967 reference households. A dash indicates an unavailable published rate for the period.') +
      ' ' + omRef('traH1_26','TRA') + ' · ' + omRef('ncsiHouseholdReference','NCSI'));
  return html;
}
function omOperatorEstimates() {
  const h = [t('نهاية الفترة','Period end'), t('الخدمة','Service'), t('حجم سوق الخدمة','Service market'),
    t('حصة المشغل','Operator share'), t('العدد التقديري','Estimated subscriptions'), t('أثر تقريب الحصة','Share-rounding range'), t('المصدر','Source')];
  let html = '';
  for (const id of ['awasr','vodafone']) {
    const rows = omanData.research.estimates.filter(x => x.operator === id).map(x => {
      const est = omEstimate(x.market, x.share, x.precision);
      const label = x.metric === 'mobile_vintage' ? t('الهاتف وفق تقرير 2022','Mobile, 2022 publication') : omLabel(x.metric);
      return [x.period, label, omNum(x.market), omNum(x.share,x.precision)+'%', '≈ '+omNum(Math.round(est.value)),
        '<bdi dir="ltr">' + fmt(Math.ceil(est.low),0) + '–' + fmt(Math.ceil(est.high)-1,0) + '</bdi>',
        external(x.source_url+'#page='+x.pdf_page, 'TRA · '+x.page)];
    });
    if (id === 'vodafone') {
      rows.unshift(['2021-12-31',t('مرحلة التشغيل التجريبي','Trial operation'),'—','—','—','—',omRef('vodafoneLaunch',t('الإطلاق','Launch'))]);
      rows.splice(2,0,['2023-12-31',t('شرائح نشطة وفق تقدير أوريدو','Active SIMs, Ooredoo peer estimate'),omNum(6985000),
        '9.2%','≈ '+omNum(643000),'—',omRef('peer2023',t('تقدير أوريدو','Ooredoo estimate'))]);
    }
    html += section(t(...omOperatorNames[id]), t('تقدير نهاية الفترة = حصة المشغل × إجمالي اشتراكات الخدمة نفسها.',
      'Estimated period-end subscriptions = operator share × the market total for that service.')) + omTable(h, rows);
  }
  return html + omNote(t('أرقام أواصر حتى 2023 للألياف فقط، ومن 2024 تشمل جميع تقنيات الإنترنت الثابت. لفودافون، حصة 2024 و2025 تخص الإنترنت المتنقل، وحصة يونيو 2026 تخص الهاتف المتنقل. تقدير أوريدو لفودافون في ديسمبر 2023 تغير من 8.6% إلى 9.2% في عرض لاحق. في ديسمبر 2022 أعلنت فودافون أكثر من 450 ألف عميل، بينما تعطي حصة الهيئة المقربة قرابة 405 آلاف.',
    'Awasr figures through 2023 cover fibre only. From 2024 the charts cover all fixed broadband. Vodafone’s 2024–25 shares cover active mobile broadband, while June 2026 covers mobile telephony. Ooredoo revised its December 2023 peer estimate from 8.6% to 9.2%. For December 2022 Vodafone reported over 450,000 customers, while the rounded TRA share implies about 405,000.') +
    ' ' + omRef('peer2023prior', t('التقدير الأول','Original estimate')) + ' · ' + omRef('vodafone2022',t('تصريح فودافون','Vodafone statement')));
}
function omListedOperators() {
  const base=omanData.ooredoo;
  const annual=base.ooredoo_oman_annual.map(x=>({...x, date:x.year+'-12-31'}));
  const quarter=base.ooredoo_oman_quarters.at(-1);
  if(quarter && quarter.period_end>annual.at(-1).date) annual.push({...quarter,date:quarter.period_end});
  const omantel=omanData.operator_records;
  const rows=annual.map(r=>{
    const fixed=omantel.find(x=>x.metric==='fixed_broadband' && x.period_end===r.date);
    const prepaid=omantel.find(x=>x.metric==='mobile_prepaid_direct' && x.period_end===r.date);
    const postpaid=omantel.find(x=>x.metric==='mobile_postpaid_ex_m2m' && x.period_end===r.date);
    const directMobile=prepaid && postpaid ? prepaid.value+postpaid.value : null;
    return [r.date,omNum(fixed?.value),omNum(directMobile),omNum(r.mobile_customers),omNum(r.fixed_line),omNum(r.total_customers),
      [fixed?external(fixed.source_url,t('عمانتل · الثابت','Omantel · fixed')):'',postpaid?external(postpaid.source_url,t('عمانتل · المتنقل','Omantel · mobile')):'',external(r.source_url,t('أوريدو','Ooredoo'))].filter(Boolean).join(' · ')];
  });
  return section(t('أعداد الاشتراكات من إفصاحات الشركات','Subscriptions from company disclosures'),
    t('اشتراكات نهاية الفترة في العمليات العُمانية. يعتمد متنقل عمانتل على مجموع مسبق وآجل الدفع عند توفر رقم لآجل الدفع يستبعد شرائح الأجهزة. أرقام أوريدو تتبع تعريف الشركة.',
      'Period-end subscriptions for the Oman operations. Omantel direct mobile adds prepaid and postpaid only when postpaid explicitly excludes M2M. Ooredoo figures follow its own definition.'))+
    omTable([t('الفترة','Period'),t('عمانتل · الإنترنت الثابت','Omantel · fixed broadband'),
      t('عمانتل · المتنقل المباشر دون M2M','Omantel · direct mobile ex M2M'),t('أوريدو · المتنقل','Ooredoo · mobile'),t('أوريدو · الثابت','Ooredoo · fixed'),t('أوريدو · الإجمالي','Ooredoo · total'),t('المصادر','Sources')],rows)+
    omNote('<a class="text-link" href="#operations?company=ORDS&market=Oman">'+t('تفاصيل أوريدو عُمان وآجل ومسبق الدفع','Ooredoo Oman prepaid and postpaid detail')+'</a>');
}
function omSourceDifferences() {
  return section(t('فروق بين الإصدارات الرسمية','Differences between official releases'),
    t('تعتمد سلسلة السنوات الكاملة جداول الهيئة المفتوحة. وتبقى بيانات كل إصدار متاحة للمراجعة.',
    'Full-year history follows TRA’s open tables. Source editions are identified below.')) +
    omTable([t('المؤشر والفترة','Indicator and period'), t('سلسلة الهيئة المستخدمة','TRA series used'),
      t('الرقم المقارن','Other published figure'), t('مصدر المقارنة','Comparison source')], [
      [t('مسبق الدفع · ديسمبر 2025','Prepaid · December 2025'),omNum(5323009),omNum(5148166),omRef('ncsi2026_09','NCSI · 30')],
      [t('الهاتف الثابت · ديسمبر 2024','Fixed voice · December 2024'),omNum(435596),omNum(435482),omRef('ncsiYearbook2026','NCSI · 196')],
      [t('الإنترنت الثابت · مارس 2025','Fixed broadband · March 2025'),omNum(585843),omNum(585853),omRef('traTech',t('جدول التقنية','Technology table'))],
    ]) + omNote(omRef('traMobile',t('جدول المتنقل','Mobile table')) + ' · ' + omRef('traFixed',t('جدول الثابت','Fixed table')));
}
function omRegulation() {
  const r = omanData.research, source = t('المصدر','Source');
  let html = section(t('كيف تُحتسب الإتاوة؟','How is the royalty calculated?'),
    t('تطبق النسبة على الإيرادات المؤهلة للخدمة المرخصة في عُمان بعد التسويات التي تسمح بها الهيئة. إجمالي إيرادات المجموعة يشمل أنشطة وأسواقًا أخرى.',
      'The rate applies to eligible Omani licensed-service revenue after adjustments permitted by TRA. Consolidated group revenue includes other activities and markets.')) +
    omTable([t('فترة الإيراد','Revenue period'),t('المتنقل','Mobile'),t('الثابت','Fixed'),source],
      r.royalties.rates.map(x => [x.period, x.mobile+'%', x.fixed+'%', x.sources.map((id,i)=>omRef(id,i? t('القوائم المدققة','Audited accounts'):t('القرار أو الإفصاح','Decision or disclosure'))).join(' · ')]));
  html += omCallout(t('أثر تغيير النسبة في 2025','Effect of the 2025 rate change'),
    t('يسري توحيد النسبة من 1 يناير 2025 لخدمات الثابت والمتنقل. لكل مليون ريال من الوعاء المؤهل للمتنقل، انخفضت الإتاوة من 120 ألفًا إلى 100 ألف ريال عند ثبات الوعاء. وأفصحت عمانتل عن أثر إيجابي بعد الضريبة قدره 1.7 مليون ريال للنصف الأول من 2025.',
      'The unified fixed and mobile rate applies from 1 January 2025. For each OMR 1m of unchanged eligible mobile revenue, the royalty fell from OMR 120,000 to OMR 100,000. Omantel disclosed a positive OMR 1.7m after-tax impact for H1 2025.')+' '+omRef('omantelNotice2025',t('إفصاح عمانتل','Omantel disclosure')));
  html += omNote(t('يشمل التوحيد خدمات المتنقل والثابت للفئات الأولى والثانية والثالثة بحسب إفصاح أغسطس 2025. تستثني التراخيص المذكورة بيع وتأجير الأجهزة الطرفية، وتجيز خصم تكاليف الربط البيني المحلي المحددة. وأكد إفصاح أوريدو عن الأشهر التسعة من 2026 استمرار أساس الحساب.',
    'The August 2025 disclosure covers mobile and fixed services in Classes I, II and III. The cited licences exclude terminal equipment sales and rental and permit specified local interconnection deductions. Ooredoo reaffirmed the calculation basis in its nine-month 2026 accounts.')+' '+omRef('vodafone',t('ترخيص المتنقل','Mobile licence'))+' · '+omRef('awasr',t('ترخيص أواصر','Awasr licence'))+' · '+omRef('ooredoo9m26',t('إيضاح 6','Note 6')));
  const paymentRows=r.royalties.ooredoo_expense.map(x=>[x.year,omNum(x.value,3),omNum(r.royalties.omantel_payable[x.year],1),
    omRef(x.source,t('أوريدو','Ooredoo'))+(r.royalties.omantel_payable[x.year]?' · '+omRef('omantel2025',t('عمانتل، إيضاح 13','Omantel, note 13')):'')]);
  html += section(t('المبالغ التي أفصح عنها المشغلون','Amounts disclosed by operators'),
    t('مليون ريال عُماني. يعرض كل عمود البند المنشور في قوائم الشركة. تحديد النقد المسدد يحتاج إلى إفصاح عن الدفع.',
      'OMR million. Each column follows the accounting item in the issuer’s financial statements. Cash remitted requires a payment disclosure.')) +
    omTable([t('السنة','Year'),t('أوريدو عُمان · مصروف الإتاوة','Ooredoo Oman · royalty expense'),t('عمانتل · إتاوة مستحقة للهيئة','Omantel · royalty payable to TRA'),source],paymentRows) +
    omNote(t('لم تتوفر في المصادر المراجعة مبالغ نقدية سنوية موثقة لفودافون أو أواصر. أفصحت أوريدو وعمانتل عن إعفاء مشروط يعادل ثلاث نقاط مئوية من إتاوة الثابت عن 2022–2024 مقابل استثمارات متفق عليها مع الهيئة.',
      'Public cash-remittance figures for Vodafone and Awasr were unavailable in the reviewed sources. Ooredoo and Omantel disclosed a conditional three-percentage-point fixed royalty waiver for 2022–24 tied to agreed investment.')+' '+omRef('ooredoo2025',t('أوريدو، إيضاح 28','Ooredoo, note 28'))+' · '+omRef('omantel2025',t('عمانتل، إيضاح 17','Omantel, note 17')));
  html += omNote(t('بلغ رسم إصدار ترخيص أواصر الثابت 35,000 ريال عُماني في 2012. وتخضع خدماتها الثابتة وخدمات فودافون المتنقلة للنسبة العامة البالغة 10% من الوعاء المؤهل منذ 2025. تعذّر التحقق من المبالغ الفردية أو أي تسويات خاصة بهما.', 'Awasr’s 2012 fixed licence carried a one-time OMR 35,000 issue fee. Its fixed services and Vodafone’s mobile services fall under the general 10% rate on eligible revenue from 2025. Individual amounts and any company-specific adjustments were unavailable.')+' '+omRef('awasr',t('ترخيص أواصر','Awasr licence'))+' · '+omRef('awasr2021',t('تعديل الإتاوة','Royalty amendment'))+' · '+omRef('omantelNotice2025',t('نسبة القطاع','Sector rate')));
  html += section(t('تراخيص المشغلين','Operator licences'),t('التراخيص الموثقة ذات الصلة بالسوق. تعرض السنوات مدة المنح أو التجديد الواردة في الوثيقة.',
    'Selected documented market licences. Years and terms refer to the cited award or renewal.')) +
    omTable([t('المشغل','Operator'),t('الخدمة','Service'),t('الفئة','Class'),t('سنة الإصدار أو التجديد','Issue or renewal year'),t('المدة بالسنوات','Term in years'),source],
      r.licences.map(x=>[t(...omOperatorNames[x.operator]),t(...omServices[x.service]),x.licence_class,x.year??'—',x.term??'—',
        x.sources.map((id,i)=>omRef(id,i?t('مرجع إضافي','Supporting record'):t('وثيقة الترخيص','Licence record'))).join(' · ')]));
  return html+omNote(t('الفئة الأولى تشمل تشغيل الشبكات العامة، والفئة الثانية تشمل تقديم خدمات عبر سعة مشغل مرخص. يسجل تقرير الهيئة لعام 2024 ترخيص إعادة البيع لأواصر الصادر أو المجدد في 2019. ويستثني ترخيص الشركة العُمانية للنطاق العريض إيرادات البنية الأساسية غير النشطة من وعاء الإتاوة.',
    'Class I includes public network operation. Class II includes services provided using another licensed network. TRA’s 2024 register lists Awasr’s 2019 resale licence. Oman Broadband’s licence excludes passive-infrastructure revenue from its royalty base.')+' '+omRef('traRegistry','TRA')+' · '+omRef('obb',t('ترخيص النطاق العريض','Oman Broadband licence')));
}
function omSpectrum() {
  const spectrum=omanData.research.spectrum, bands=[700,800,900,1800,2100,2600];
  let html=section(t('حقوق الطيف في ملاحق تراخيص المتنقل','Spectrum rights in mobile licence schedules'),
    t('عرض الحزمة بالميجاهرتز عند المنح أو التجديد. ترمز 2 × 10 إلى 10 ميجاهرتز في كل اتجاه. الشرطة تعني أن النطاق لم يرد في ذلك الملحق.',
    'Bandwidth in MHz at grant or renewal. 2 × 10 means 10 MHz in each direction. A dash means the band was absent from that schedule.')) +
    omTable([t('المشغل والسنة','Operator and year'),...bands.map(String),t('رسم المدة · مليون ر.ع.','Term fee · OMR m'), t('المصدر','Source')],
      spectrum.awards.map(x=>[t(...omOperatorNames[x.operator])+' · '+x.year,...bands.map(b=>x.paired_mhz[b]?'<bdi dir="ltr">2 × '+x.paired_mhz[b]+'</bdi>':'—'),
        omNum(x.fee_mn,Number.isInteger(x.fee_mn)?0:1),omRef(x.source,t('البند 27 والملحق ج','Clause 27 and Schedule C'))]));
  html+=omNote(t('تغطي الرسوم ترخيص الخدمة وحقوق الطيف المدرجة لمدة 15 سنة. يحتاج تحديد الرصيد الحالي لكل مشغل إلى التخصيصات والتعديلات اللاحقة.',
    'The fees cover the service licence and listed spectrum rights for 15 years. A current holdings inventory also requires subsequent assignments and amendments.'));
  html+=omNote(t('خارج هذه الملاحق، أفصحت أوريدو في 2019 عن الاتفاق على 100 ميجاهرتز في نطاق 3.5 جيجاهرتز للثابت والمتنقل. وفي مكالمة الربع الأول من 2021 ذكرت أن رسم طيف الجيل الخامس السنوي في عُمان يقارب مليون ريال. يخص المبلغ تاريخ الإفصاح.',
    'Separately, in 2019 Ooredoo reported an agreement for 100 MHz in the 3.5 GHz range for fixed and mobile services. On its Q1 2021 call, management put the Oman annual 5G spectrum fee at approximately OMR 1m. The amount relates to that historical disclosure.')+' '+omRef('ooredoo5g2019',t('عرض 2019','2019 presentation'))+' · '+omRef('ooredoo5g2021',t('مكالمة 2021','2021 call')));
  html+=section(t('الخطة الوطنية للترددات','National spectrum plan'),t('نطاقات مختارة من إصدار الهيئة لعام 2024. يوضح الجدول أين تسمح الخطة باستخدامات الاتصالات المتنقلة الدولية (IMT).',
    'Selected ranges from TRA’s 2024 plan showing where International Mobile Telecommunications (IMT) use is identified.'))+
    omTable([t('النطاق','Band'),t('المدى الوطني بالميجاهرتز','National range in MHz'),t('الصفحة','Page')],
      spectrum.bands.map(b=>[b.band,'<bdi dir="ltr">'+b.ranges.map(v=>v.join('–')).join(' / ')+'</bdi>',
        external(omanData.research.sources.nfat2024+'#page='+b.pages[0],b.pages.join('–'))]))+
    omNote(t('ضمن نطاق 26 جيجاهرتز، تصنّف الخطة 24.25–26.5 جيجاهرتز للاستخدام المدني و26.5–27.5 للاستخدام العسكري. وتذكر أوريدو استخدام 3.5 جيجاهرتز، وفودافون 700 و2600 ميجاهرتز في شبكة الجيل الخامس.',
      'Within the 26 GHz range, the plan marks 24.25–26.5 GHz as civil and 26.5–27.5 GHz as military. Ooredoo identifies 3.5 GHz, and Vodafone identifies 700 and 2600 MHz for its 5G network.')+
      ' '+omRef('nfat2024','TRA')+' · '+omRef('ooredoo5G','Ooredoo')+' · '+omRef('vodafone5g','Vodafone'));
  html+=section(t('رسوم التسجيل والاستخدام','Registration and usage fees'),t('يحدد نوع الخدمة وعرض النطاق وشروط الترخيص الرسم المنطبق.',
    'The service category, bandwidth and licence terms determine the applicable charge.'))+
    omTable([t('الفئة','Service'),t('التسجيل · ر.ع.','Registration · OMR'),t('الاستخدام · ر.ع.','Usage · OMR'),t('السند','Authority')],[
      ['IMT',t('عرض النطاق × عامل التغطية × عامل التردد × 4,000','MHz × coverage factor × frequency factor × 4,000'),
        t('عرض النطاق × عامل التغطية × عامل التردد × 10,000','MHz × coverage factor × frequency factor × 10,000'),omRef('imtFees',t('جداول 51–53','Tables 51–53'))],
      ['VSAT',t('50 لكل محطة طرفية','50 per terminal'),t('25 سنويًا لكل محطة طرفية','25 per terminal annually'),omRef('fees2026',t('قرار يونيو 2026','June 2026 decision'))],
      ['A-ESIM / M-ESIM', t('50 لكل مزود بحسب الفئة','50 per provider by category'),t('600 سنويًا لكل مزود بحسب الفئة','600 per provider annually'),omRef('fees2026',t('قرار يونيو 2026','June 2026 decision'))]
    ])+omNote(t('في صيغة IMT، عامل التردد 1 تحت 24 جيجاهرتز و0.05 ابتداءً من 24 جيجاهرتز. يلزم معرفة عامل التغطية والحقوق المشمولة برسم المدة لحساب أي مبلغ إضافي مستحق على مشغل.',
      'In the IMT formula, the frequency factor is 1 below 24 GHz and 0.05 at or above 24 GHz. Calculating an additional operator charge requires its coverage factor and the rights already covered by the term fee.')+' '+omRef('imtFees',t('قرار الهيئة','TRA decision')));
  html+=omCallout(t('مثال لحساب رسم الطيف','Spectrum tariff example'),
    t('لنطاق إجمالي قدره 10 ميجاهرتز تحت 24 جيجاهرتز، مع عامل تغطية 1 لأربع محافظات فأكثر، يبلغ رسم التسجيل 40,000 ريال ورسم الاستخدام السنوي 100,000 ريال. هذا مثال على التعرفة، وتحدد وثائق كل ترخيص المبلغ المستحق.',
      'For 10 MHz in total below 24 GHz and coverage factor 1 for four or more governorates, registration is OMR 40,000 and annual use is OMR 100,000. These illustrative tariff charges depend on the terms of each licence.')+' '+omRef('imtFees',t('تعرفة التردد','Frequency tariff'))+' · '+omRef('coverageFee',t('عامل التغطية','Coverage factor')));
  return html;
}
function omResearchView(mode) {
  const titles={penetration:t('الاشتراكات والانتشار في عُمان','Oman subscriptions and penetration'),
    regulation:t('تراخيص الاتصالات والإتاوة في عُمان','Oman telecom licences and royalties'),spectrum:t('الطيف الترددي ورسومه في عُمان','Oman radio spectrum and fees')};
  let content;
  if (mode==='penetration') {
    const groups=[['rates',t('معدلات الانتشار','Penetration rates'),omPenetration],
      ['companies',t('عمانتل وأوريدو','Omantel & Ooredoo'),omListedOperators],
      ['estimates',t('أواصر وفودافون','Awasr & Vodafone'),omOperatorEstimates],
      ['editions',t('فروق المصادر','Source differences'),omSourceDifferences]];
    const links=groups.map(([id,label])=>'<button class="button" data-oa-section="'+id+'">'+label+'</button>').join('');
    content='<nav class="oa-index" aria-label="'+titles[mode]+'">'+links+'</nav>'+
      groups.map(([id,,render])=>'<section id="oa-'+id+'">'+render()+'</section>').join('');
  } else {
    content=mode==='regulation'?omRegulation():omSpectrum();
  }
  return pageHeading(titles[mode])+oaTabs()+omNote(t('تاريخ مراجعة المصادر','Sources reviewed')+' · '+omanData.research.as_of)+content;
}

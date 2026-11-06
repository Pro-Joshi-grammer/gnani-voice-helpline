# Telangana welfare schemes: grounded source pack for the Gnani helpline

_Last verified 2026-10-28. Facts and bases are in English; question_te, fail_message_te, notice_te and summary_te are Telugu for direct use in speech._

## How to read this pack

| Confidence | Meaning |
|---|---|
| high | Stated by an official government page/portal or by an official order/statement reported consistently by reputable outlets. |
| medium | Reported by one reputable outlet or by explainers that agree with each other. State with care and keep the caveat. |
| low | Single or conflicting secondary report. Never state as fact; use only to say the sources disagree. |

**Source tiers**

- `official`: Official Telangana/Central government page or portal
- `public_broadcaster`: All India Radio (public broadcaster) news report
- `major_news`: Established news outlet (reporting a GO, official statement or event)
- `secondary`: Aggregator/explainer; use only for low-stakes details and never alone

**Rules for the assistant**

1. Only state claims that appear in a scheme's facts or criteria, and cite their source_ids.
2. status values other than 'active' (disputed, not_confirmed_launched, completed_one_time, active_amount_hike_not_implemented, active_implementation_unclear) must be mentioned before benefits are described.
3. For anything listed in unknown_in_sources, say once that published sources do not cover it and point to the official office or portal. Do not guess.
4. Facts with confidence 'low' must not be stated as fact.
5. Eligibility results use wording like 'appears to meet the published criteria'; final decisions rest with officials.

**Limitations of this pack**

- Most sources here are established news outlets reporting government orders; official portals were reachable only for some schemes. Re-check the official page before launch for anything marked medium or low.
- Rythu Bharosa and Indiramma Indlu content is carried over from the user's own verification files (22 Oct 2026) and was not re-fetched.
- Government schemes change often; this pack reflects what could be found on 28 Oct 2026.

## Status overview

| scheme_id | Scheme | Status |
|---|---|---|
| `mahalakshmi_free_bus` | Mahalakshmi: Free bus travel for women (TGSRTC) | `active` |
| `mahalakshmi_monthly_aid_2500` | Mahalakshmi: Rs 2,500 per month for women (promised, not confirmed as launched) | `not_confirmed_launched` |
| `mahalakshmi_lpg_500` | Mahalakshmi: LPG cylinder at Rs 500 | `active` |
| `gruha_jyothi` | Gruha Jyothi: 200 units of free electricity | `active` |
| `rajiv_aarogyasri` | Rajiv Aarogyasri: health cover up to Rs 10 lakh per family per year | `active` |
| `indiramma_indlu` | Indiramma Indlu (housing) | `active` |
| `rythu_bharosa` | Rythu Bharosa (farmer investment support) | `active` |
| `rythu_bima` | Rythu Bima (farmers' group life insurance, Rs 5 lakh) | `disputed` |
| `rythu_runa_mafi` | Rythu Runa Mafi (crop loan waiver up to Rs 2 lakh) | `completed_one_time` |
| `cheyutha_aasara_pensions` | Cheyutha (Aasara) social security pensions | `active_amount_hike_not_implemented` |
| `kalyana_lakshmi_shaadi_mubarak` | Kalyana Lakshmi / Shaadi Mubarak (marriage assistance) | `active` |
| `rajiv_yuva_vikasam` | Rajiv Yuva Vikasam (self-employment subsidy for youth) | `active_implementation_unclear` |
| `ration_cards_fine_rice` | New ration cards and free fine rice (6 kg per person) | `active` |

---

## Mahalakshmi: Free bus travel for women (TGSRTC)

**Telugu name:** మహాలక్ష్మి: మహిళలకు ఉచిత బస్సు ప్రయాణం  
**scheme_id:** `mahalakshmi_free_bus`  
**Status:** `active`  
**Last verified:** 2026-10-28

> Running since 9 Dec 2023. Smart-card rollout was announced for 2 June 2026; Aadhaar/ID still accepted per the pre-launch report.

**Summary:** Women, girls and transgender persons residing in Telangana travel free (zero ticket) in covered TGSRTC buses within the state. No application is needed for the travel itself.

**సారాంశం:** తెలంగాణలో నివసించే మహిళలు, బాలికలు, ట్రాన్స్‌జెండర్ వ్యక్తులు TGSRTC లోని కొన్ని రకాల బస్సుల్లో రాష్ట్రం లోపల ఉచితంగా ప్రయాణించవచ్చు. ఇందుకోసం ప్రత్యేకంగా దరఖాస్తు చేయాల్సిన అవసరం లేదు.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| launch | The free travel scheme started on 9 December 2023. | high | sf-mahalakshmi-launch, air-mahalakshmi-200cr, pti-free-bus-order |
| who | Women, girls and transgender persons who are residents (domiciles) of Telangana are covered. | medium | impri-mahalakshmi, dc-mahalakshmi-smartcard |
| buses_initial | The initial government order made travel free in Palle Velugu and Express buses up to the borders of Telangana. | high | pti-free-bus-order |
| buses_2026 | TGSRTC said in March 2026 the scheme operates in about 81% of its buses: Pallevelugu, District Express, City Ordinary and City Metro Express. | high | siasat-mahalakshmi-81pct |
| not_covered | Deluxe and super luxury buses (and AC buses) are reported as not covered. *(Exact list of excluded services not seen in an official order; confirm with TGSRTC.)* | medium | vikaspedia-free-bus |
| id_proof | Passengers get a zero-fare ticket by showing an Aadhaar card (or other government ID) to the conductor. | high | dc-mahalakshmi-smartcard |
| smart_card | A chip-based Mahalakshmi Smart Card (Rs 50 fee, apply at MeeSeva centres or TGSRTC bus pass counters with Aadhaar, passport photo and mobile number) was announced for launch on 2 June 2026; officials said it may become mandatory later. *(This is a pre-launch report; the actual rollout status was not confirmed.)* | medium | dc-mahalakshmi-smartcard |
| scale | Over 200 crore zero tickets were issued by July 2025; TGSRTC reported more than 290 crore free journeys by March 2026. | high | air-mahalakshmi-200cr, siasat-mahalakshmi-81pct |

### Eligibility criteria (ask in this order)

1. **woman_girl_or_transgender** — type `yes_no`, required `yes`, confidence `high`, source `sf-mahalakshmi-launch`
   - Question: మీరు మహిళ, బాలిక లేదా ట్రాన్స్‌జెండర్ వ్యక్తియా?
   - Basis: Free travel for women, girls and transgender persons.
   - If not met: ఈ పథకం మహిళలు, బాలికలు మరియు ట్రాన్స్‌జెండర్ వ్యక్తుల కోసం మాత్రమే.
2. **telangana_resident** — type `yes_no`, required `yes`, confidence `medium`, source `impri-mahalakshmi`
   - Question: మీరు తెలంగాణలో నివసిస్తున్నారా?
   - Basis: Scheme is for residents (domiciles) of Telangana.
   - If not met: ఈ ఉచిత ప్రయాణం తెలంగాణలో నివసించే వారికి మాత్రమే ఉద్దేశించినది.
3. **covered_bus_type** — type `yes_no`, required `yes`, confidence `high`, source `siasat-mahalakshmi-81pct`
   - Question: మీరు ఎక్కే బస్సు పల్లె వెలుగు, ఎక్స్‌ప్రెస్, సిటీ ఆర్డినరీ లేదా సిటీ మెట్రో ఎక్స్‌ప్రెస్ రకమా?
   - Basis: TGSRTC lists Pallevelugu, District Express, City Ordinary and City Metro Express as covered.
   - If not met: డీలక్స్, సూపర్ లగ్జరీ, ఏసీ వంటి ఇతర రకాల బస్సుల్లో ఈ ఉచిత ప్రయాణం వర్తించదని నివేదికలు చెబుతున్నాయి.
4. **within_telangana** — type `yes_no`, required `yes`, confidence `high`, source `pti-free-bus-order`
   - Question: మీ ప్రయాణం తెలంగాణ రాష్ట్ర సరిహద్దుల లోపలేనా?
   - Basis: Free travel is up to the borders of Telangana.
   - If not met: ఉచిత ప్రయాణం తెలంగాణ సరిహద్దుల వరకు మాత్రమే.

### Not covered by sources (say once, then point to the official office)

- **smart_card_mandatory**: Whether the Mahalakshmi Smart Card has become mandatory and how far the rollout has progressed  
  Telugu notice: స్మార్ట్ కార్డు తప్పనిసరి అయిందా, ఎంతవరకు అమలైందో ఖచ్చితంగా తెలియదు — బస్సు కండక్టర్ లేదా TGSRTC వద్ద నిర్ధారించుకోండి.
- **excluded_services_list**: Official complete list of services where the scheme does not apply  
  Telugu notice: ఏఏ బస్సు సర్వీసుల్లో వర్తించదనే పూర్తి అధికారిక జాబితా నా వద్ద లేదు — TGSRTC వద్ద చూడండి.
- **non_resident_women**: Rules for women who live outside Telangana or hold a non-Telangana Aadhaar  
  Telugu notice: తెలంగాణ బయట నివసించే మహిళలకు నియమాలు మూలాల్లో స్పష్టంగా లేవు.

**How to apply:** No application for the travel. Show Aadhaar or other government ID to the conductor and collect the zero ticket. Smart card: MeeSeva centre or TGSRTC bus pass counter.  
**Portal:** https://tgsrtc.telangana.gov.in (as named by TGSRTC; not fetched in this pass)  

**Sources used:**
- `air-mahalakshmi-200cr`: Mahalakshmi Scheme crosses 200 crore free bus rides (All India Radio News, 2025-07-23) [public_broadcaster] <https://www.newsonair.gov.in/mahalakshmi-scheme-crosses-200-crore-free-bus-rides-in-telangana-women-save-%E2%82%B96700-crore>
- `dc-mahalakshmi-smartcard`: Mahalakshmi Smart Cards To Be Launched On June 2 (Deccan Chronicle, 2026-05) [major_news] <https://www.deccanchronicle.com/southern-states/telangana/telangana-rtc-mahalakshmi-smart-cards-for-free-bus-travel-how-and-where-to-apply-1959859>
- `impri-mahalakshmi`: What does Mahalakshmi scheme reveal about women's mobility in Telangana? (IMPRI) [secondary] <https://iprr.impriindia.com/?p=3664>
- `pti-free-bus-order`: Telangana govt to launch free bus travel for women scheme on December 9 (PTI) (Udayavani / PTI, 2023-12-09) [major_news] <https://udayavani.com/?p=1571891>
- `sf-mahalakshmi-launch`: Congress govt in Telangana flags off Mahalakshmi scheme (The South First, 2023-12-09) [major_news] <https://thesouthfirst.com/topstory/congress-govt-in-telangana-flags-off-mahalakshmi-scheme-offering-women-free-rides-on-state-run-buses/>
- `siasat-mahalakshmi-81pct`: Telangana women saved Rs 10K crore from free bus travel: Govt (Siasat (quoting TGSRTC VC & MD), 2026-03-29) [major_news] <https://www.siasat.com/telangana-women-save-rs-10k-crore-from-free-bus-travel-govt-3442863/amp/>
- `vikaspedia-free-bus`: Free bus travel for women (Vikaspedia) [secondary] <https://en.vikaspedia.in/viewcontent/women/women-empowerment/free-bus-travel-for-women>

---

## Mahalakshmi: Rs 2,500 per month for women (promised, not confirmed as launched)

**Telugu name:** మహాలక్ష్మి: మహిళలకు నెలకు రూ. 2,500 (హామీ; అమలు నిర్ధారణ కాలేదు)  
**scheme_id:** `mahalakshmi_monthly_aid_2500`  
**Status:** `not_confirmed_launched`  
**Last verified:** 2026-10-28

> Promised in the Congress Six Guarantees. Reputable reports through 2025 describe it as pending. A viral video claiming a Bathukamma rollout was confirmed a deepfake in October 2026. Several aggregator sites claim a 2026 launch, but no reputable report was found. The assistant must NOT tell users it is being paid.

**Summary:** The Rs 2,500/month assistance is part of the promised Mahalakshmi guarantee. No reputable source found confirms that it has been launched, and its eligibility rules have not been published in any source found.

**సారాంశం:** నెలకు రూ. 2,500 సాయం మహాలక్ష్మి హామీలో భాగం. అయితే ఇది అమలులోకి వచ్చినట్లు నమ్మదగిన మూలాల్లో నిర్ధారణ కాలేదు, అర్హతా నిబంధనలు కూడా ప్రకటించినట్లు కనిపించలేదు.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| promised | Rs 2,500 per month for women is one of the Congress Six Guarantees; Mahalakshmi has three components (free bus travel, Rs 500 gas cylinder, Rs 2,500 monthly aid). | high | sf-2500-factcheck, sf-guarantees-hindu-ktr |
| pending_2025 | In July 2025 the monthly allowance was reported as long pending since the Congress took office, with the government citing financial challenges. | high | hans-2500-pending |
| fact_check | A fact-check found that the Rs 2,500 aid had not materialised despite Congress leaders' claims. *(Dated early 2025; later developments should be checked.)* | medium | sf-2500-factcheck |
| deepfake_oct2026 | On 8 October 2026 a viral video of the Chief Minister promising Rs 2,500 monthly aid from Bathukamma and two tolas of gold under Kalyana Lakshmi was reported as officially confirmed to be a deepfake. | medium | oneindia-deepfake-2500 |

### Eligibility criteria (ask in this order)

_No eligibility criteria: do not run an eligibility check for this scheme._

### Not covered by sources (say once, then point to the official office)

- **launch_status**: Whether the Rs 2,500 monthly assistance has been launched and paid anywhere  
  Telugu notice: రూ. 2,500 నెలవారీ సాయం అమలులోకి వచ్చినట్లు నిర్ధారణ లేదు — అధికారిక ప్రకటన కోసం చూడండి.
- **eligibility**: Eligibility rules, income limits, application process  
  Telugu notice: అర్హతలు, ఆదాయ పరిమితి, దరఖాస్తు విధానం ఇంకా ప్రకటించినట్లు మూలాల్లో లేవు.

**How to apply:** No application process found. Beware of fake messages and videos.  

**Sources used:**
- `hans-2500-pending`: Mahalakshmi scheme: Decision on Rs 2.5K monthly payout to women likely (The Hans India, 2025-07) [major_news] <https://www.thehansindia.com/telangana/mahalakshmi-scheme-decision-on-rs-25k-monthly-payout-to-women-likely-990453>
- `oneindia-deepfake-2500`: Revanth Reddy Rs 2,500 aid / 2 tulas gold video confirmed deepfake (Oneindia Telugu, 2026-10-08) [major_news] <https://telugu.oneindia.com/news/telangana/cm-revanth-reddy-on-rs-2-500-aid-for-women-2tulas-gold-in-kalyana-lakshmi-from-bathukamma-deepfake-509703.html>
- `sf-2500-factcheck`: Congress claims 90 lakh women receive Rs 2,500 in Telangana: Here's the reality (The South First, 2025-01) [major_news] <https://thesouthfirst.com/telangana/congress-claims-90-lakh-women-receive-rs-2500-in-telangana-heres-the-reality/>
- `sf-guarantees-hindu-ktr`: KTR says Revanth made Rahul lie about promises (The Hindu via PressReader) (The Hindu, 2024-05-06) [major_news] <https://www.pressreader.com/india/the-hindu-international-9BN2/20240506/281651080189161>

---

## Mahalakshmi: LPG cylinder at Rs 500

**Telugu name:** మహాలక్ష్మి: రూ. 500కే గ్యాస్ సిలిండర్  
**scheme_id:** `mahalakshmi_lpg_500`  
**Status:** `active`  
**Last verified:** 2026-10-28

> Launched 27 Feb 2024 by government order for white ration card holders with active domestic LPG connections.

**Summary:** Eligible white ration card families with an active domestic LPG connection get a domestic LPG refill at a subsidised Rs 500.

**సారాంశం:** తెల్ల రేషన్ కార్డు ఉండి, క్రియాశీల గృహ గ్యాస్ కనెక్షన్ ఉన్న కుటుంబాలకు గృహ వినియోగ గ్యాస్ సిలిండర్ రూ. 500కే లభిస్తుంది.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| launch | Launched on 27 February 2024 together with Gruha Jyothi. | high | sf-lpg-gj-guidelines, sakshi-lpg-gj, ap7am-lpg-launch |
| rule_card | The government order sanctions a domestic LPG refill at Rs 500 for white ration card (food security card) holders. | high | sf-lpg-gj-guidelines, ap7am-lpg-guidelines |
| rule_connection | Beneficiaries must have an active domestic LPG connection. | high | ap7am-lpg-launch, sf-lpg-gj-guidelines |
| praja_palana | At launch only those who had applied during Praja Palana were eligible; the Civil Supplies Minister said those who had not applied could still enrol if they hold a white ration card and an LPG connection. | medium | ap7am-lpg-launch, sf-lpg-gj-guidelines |
| scale | The minister said about 40 lakh families were expected to benefit. | medium | sakshi-lpg-gj |

### Eligibility criteria (ask in this order)

1. **white_ration_card** — type `yes_no`, required `yes`, confidence `high`, source `sf-lpg-gj-guidelines`
   - Question: మీ కుటుంబానికి తెల్ల రేషన్ కార్డు (ఆహార భద్రతా కార్డు) ఉందా?
   - Basis: GO sanctions Rs 500 LPG refill to white ration card (food security card) holders.
   - If not met: ఈ పథకం తెల్ల రేషన్ కార్డు ఉన్న కుటుంబాలకు మాత్రమే.
2. **active_lpg_connection** — type `yes_no`, required `yes`, confidence `high`, source `ap7am-lpg-launch`
   - Question: మీకు ప్రస్తుతం క్రియాశీలంగా ఉన్న గృహ వినియోగ గ్యాస్ కనెక్షన్ ఉందా?
   - Basis: Eligible households must have an active domestic LPG connection.
   - If not met: ఈ పథకానికి క్రియాశీల గృహ గ్యాస్ కనెక్షన్ ఉండాలి.

### Not covered by sources (say once, then point to the official office)

- **connection_holder_name**: Whether the LPG connection must be in a woman's name (one report says yes; others say in the applicant's name)  
  Telugu notice: గ్యాస్ కనెక్షన్ మహిళ పేరు మీద ఉండాలా అనే విషయంలో మూలాలు ఒకేలా చెప్పడం లేదు — ధృవీకరించుకోండి.
- **cylinder_cap**: Annual cap on subsidised cylinders  
  Telugu notice: సంవత్సరానికి ఎన్ని సిలిండర్లకు వర్తిస్తుందో మూలాల్లో స్పష్టంగా లేదు.
- **payment_mechanism**: Whether the user pays Rs 500 at delivery or pays full price and gets the difference by transfer  
  Telugu notice: రూ. 500 చెల్లించే విధానం (డెలివరీ సమయంలోనా, తర్వాత ఖాతాలో జమనా) మూలాల్లో స్పష్టంగా లేదు.
- **current_enrolment**: Whether new enrolments are open now  
  Telugu notice: ఇప్పుడు కొత్తగా నమోదు చేసుకునే అవకాశం ఉందో లేదో మూలాల్లో లేదు — గ్యాస్ ఏజెన్సీ/పౌర సరఫరాల శాఖ వద్ద చూడండి.

**How to apply:** Originally via Praja Palana forms; the minister later said eligible families who had not applied could still enrol. Current procedure not confirmed.  

**Sources used:**
- `ap7am-lpg-guidelines`: Telangana Govt Announces Guidelines for Rs. 500 Gas Cylinder Scheme (AP7AM, 2024-02) [secondary] <https://www.ap7am.com/en/75961/telangana-govt-announces-guidelines-for-rs-500-gas-cylinder-scheme>
- `ap7am-lpg-launch`: Congress government in Telangana implements two more guarantees (AP7AM (wire report), 2024-02-27) [secondary] <https://www.ap7am.com/en/75977/congress-government-in-telangana-implements-two-more-guarantees>
- `sakshi-lpg-gj`: Free electricity, Rs 500 gas cylinder schemes, conditions apply (Sakshi Post, 2024-02-27) [major_news] <https://www.sakshipost.com/news/congress-government-telangana-implements-two-more-guarantees-277489>
- `sf-lpg-gj-guidelines`: LPG cylinder at Rs 500, free power up to 200 units: Guarantees launched in Telangana (The South First, 2024-02-27) [major_news] <https://thesouthfirst.com/telangana/lpg-cylinder-at-%E2%82%B9500-free-power-up-to-200-units-guarantees-launched-in-telangana/>

---

## Gruha Jyothi: 200 units of free electricity

**Telugu name:** గృహ జ్యోతి: 200 యూనిట్ల ఉచిత విద్యుత్  
**scheme_id:** `gruha_jyothi`  
**Status:** `active`  
**Last verified:** 2026-10-28

> Government order dated 26 Feb 2024; launched 27 Feb 2024; zero bills started 1 Mar 2024.

**Summary:** Eligible households with a white ration card get a zero electricity bill for domestic consumption up to 200 units per month on a single service connection.

**సారాంశం:** తెల్ల రేషన్ కార్డు ఉన్న అర్హ కుటుంబాలకు ఒకే గృహ విద్యుత్ కనెక్షన్‌పై నెలకు 200 యూనిట్ల వరకు వినియోగానికి జీరో బిల్లు వస్తుంది.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| go_date | The government order is dated 26 February 2024; the scheme was launched on 27 February 2024 and zero bills began on 1 March 2024. | high | siasat-gruha-jyothi-launch, tnm-gj-start, sf-lpg-gj-guidelines |
| benefit | Eligible households get a zero bill for domestic consumption up to 200 units a month. | high | siasat-gruha-jyothi-launch, tnm-gj-start |
| conditions | Households need a white ration card linked with Aadhaar and a single domestic service connection linked to the ration card (USC number from the electricity bill). | high | sf-lpg-gj-guidelines, dtnext-gj-start |
| above_200 | A household that uses more than 200 units in a month does not get the zero bill for that month, according to reports on the government order. *(Applies month by month; confirm with the discom.)* | medium | nt-gj-above-200, siasat-gruha-jyothi-launch |
| grievance | Consumers who believe they qualify but were billed can approach the MPDO office, Municipal Commissioner or the relevant electricity circle office. | medium | sf-lpg-gj-guidelines |
| domestic_only | The free power applies to domestic use only. | high | siasat-gruha-jyothi-launch |

### Eligibility criteria (ask in this order)

1. **white_ration_card** — type `yes_no`, required `yes`, confidence `high`, source `sf-lpg-gj-guidelines`
   - Question: మీ కుటుంబానికి తెల్ల రేషన్ కార్డు (ఆహార భద్రతా కార్డు) ఉందా?
   - Basis: Eligible beneficiaries must hold a valid white ration card.
   - If not met: ఈ పథకం తెల్ల రేషన్ కార్డు ఉన్న కుటుంబాలకు మాత్రమే.
2. **ration_card_aadhaar_linked** — type `yes_no`, required `yes`, confidence `high`, source `dtnext-gj-start`
   - Question: మీ రేషన్ కార్డు ఆధార్‌తో అనుసంధానమై ఉందా?
   - Basis: White ration card must be linked with Aadhaar.
   - If not met: రేషన్ కార్డు ఆధార్‌తో అనుసంధానం కావాలి.
3. **domestic_connection_linked** — type `yes_no`, required `yes`, confidence `high`, source `sf-lpg-gj-guidelines`
   - Question: మీ గృహ విద్యుత్ కనెక్షన్ (ఒకే సర్వీస్ కనెక్షన్) మీ రేషన్ కార్డుతో అనుసంధానమై ఉందా?
   - Basis: Single domestic service connection linked to the ration card.
   - If not met: గృహ వినియోగ కనెక్షన్ ఒక్కటే, అది రేషన్ కార్డుతో అనుసంధానమై ఉండాలి.
4. **monthly_usage_within_200** — type `yes_no`, required `yes`, confidence `medium`, source `siasat-gruha-jyothi-launch`
   - Question: మీ నెలవారీ గృహ విద్యుత్ వినియోగం 200 యూనిట్లలోపేనా?
   - Basis: Zero bill for consumption up to 200 units per month.
   - If not met: 200 యూనిట్లు దాటిన నెలలో జీరో బిల్లు వర్తించదని నివేదికలు చెబుతున్నాయి.

### Not covered by sources (say once, then point to the official office)

- **income_ceiling**: Whether any income ceiling applies beyond holding a white ration card  
  Telugu notice: తెల్ల రేషన్ కార్డు తప్ప ఆదాయ పరిమితి ఉందా అనేది ప్రచురించిన మూలాల్లో లేదు.
- **rented_house**: Rules for tenants whose connection is in the landlord's name  
  Telugu notice: అద్దె ఇంట్లో ఉండి కనెక్షన్ యజమాని పేరు మీద ఉన్నవారికి నియమాలు మూలాల్లో లేవు.

**How to apply:** Originally through Praja Palana. Unlinked eligible consumers can approach MPDO / Municipal Commissioner / electricity circle office with the white ration card and electricity bill.  

**Sources used:**
- `dtnext-gj-start`: Telangana starts implementing Gruha Jyothi scheme (DT Next / IANS, 2024-03-01) [major_news] <https://www.dtnext.in/news/national/telangana-starts-implementing-gruha-jyothi-scheme-771192>
- `nt-gj-above-200`: Gruha Jyothi zero bill rule (newspaper e-paper clipping) (Namasthe Telangana / Telangana Today e-paper, 2024-03-10) [major_news] <https://epapercdn.ntnews.com/NT/2024/03/10/TTE/5_01/2aaab99147382af2_01.pdf>
- `sf-lpg-gj-guidelines`: LPG cylinder at Rs 500, free power up to 200 units: Guarantees launched in Telangana (The South First, 2024-02-27) [major_news] <https://thesouthfirst.com/telangana/lpg-cylinder-at-%E2%82%B9500-free-power-up-to-200-units-guarantees-launched-in-telangana/>
- `siasat-gruha-jyothi-launch`: Gruha Jyothi: Telangana govt launches free power scheme (Siasat, 2024-02-27) [major_news] <https://www.siasat.com/gruha-jyothi-telangana-govt-launches-free-power-scheme-2983871/amp/>
- `tnm-gj-start`: Telangana starts implementing Gruha Jyothi scheme (The News Minute, 2024-03-01) [major_news] <https://www.thenewsminute.com/telangana/telangana-starts-implementing-gruha-jyothi-scheme>

---

## Rajiv Aarogyasri: health cover up to Rs 10 lakh per family per year

**Telugu name:** రాజీవ్ ఆరోగ్యశ్రీ: కుటుంబానికి సంవత్సరానికి రూ. 10 లక్షల వరకు వైద్య సాయం  
**scheme_id:** `rajiv_aarogyasri`  
**Status:** `active`  
**Last verified:** 2026-10-28

> Cover doubled from Rs 5 lakh to Rs 10 lakh from December 2023. Hospital payment disputes were reported in September 2025; confirm current service at the hospital.

**Summary:** Cashless treatment at empanelled hospitals for BPL families identified through the food security (white ration) card, up to Rs 10 lakh per family per year. The limit is for approved packages, not every expense.

**సారాంశం:** ఆహార భద్రతా (తెల్ల రేషన్) కార్డు ఉన్న పేద కుటుంబాలకు ఎంపానెల్డ్ ఆసుపత్రుల్లో సంవత్సరానికి కుటుంబానికి రూ. 10 లక్షల వరకు నగదు రహిత చికిత్స. ఇది ఆమోదిత ప్యాకేజీలకే వర్తిస్తుంది, ప్రతి ఖర్చుకు కాదు.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| launch | The Rs 10 lakh cover was launched on 9 December 2023 under the Rajiv Aarogyasri / Cheyutha banner; the ceiling earlier was Rs 5 lakh. | high | sf-mahalakshmi-launch, sf-aarogyasri-2025 |
| benefit | Cashless treatment up to Rs 10 lakh per family per year for BPL households. | high | sf-aarogyasri-2025, dc-budget-2526-aarogyasri |
| reach | The Aarogyasri Trust described the scheme as covering over 99 lakh BPL families; the 2025-26 budget coverage said 90.10 lakh BPL families. *(Figures differ between sources.)* | medium | sf-aarogyasri-2025, dc-budget-2526-aarogyasri |
| identification | Beneficiaries are identified through the Food Security Card (white ration card) and the Civil Supplies database. | medium | ditto-aarogyasri, sakshi-aarogyasri-orphans |
| package_based | Coverage is package-based and depends on hospital empanelment and authorisation; Rs 10 lakh is a limit, not a guarantee that every expense is paid. | medium | ditto-aarogyasri |
| orphans | In 2025 health cards were extended to orphans for treatment up to Rs 10 lakh; in emergencies an income certificate signed by the Tahsildar can serve as an alternative to a ration card. | medium | sakshi-aarogyasri-orphans |
| dues_risk | In September 2025 private hospitals threatened to suspend Aarogyasri services over pending dues. *(Dated; services may have resumed. Do not state current availability.)* | medium | sf-aarogyasri-2025 |

### Eligibility criteria (ask in this order)

1. **telangana_resident** — type `yes_no`, required `yes`, confidence `medium`, source `sf-aarogyasri-2025`
   - Question: మీరు తెలంగాణలో నివసిస్తున్నారా?
   - Basis: Scheme is for BPL families of Telangana.
   - If not met: ఈ పథకం తెలంగాణ రాష్ట్ర కుటుంబాల కోసం.
2. **white_ration_card** — type `yes_no`, required `yes`, confidence `medium`, source `ditto-aarogyasri`
   - Question: మీ కుటుంబానికి తెల్ల రేషన్ కార్డు (ఆహార భద్రతా కార్డు) ఉందా?
   - Basis: Beneficiaries are identified through the Food Security Card database.
   - If not met: సాధారణంగా తెల్ల రేషన్ కార్డు ఉన్న కుటుంబాలకే వర్తిస్తుంది. అనాథల వంటి ప్రత్యేక వర్గాలకు వేరే విధానం ఉండవచ్చు.

### Not covered by sources (say once, then point to the official office)

- **income_property_limits**: Any separate income or property limits beyond the ration card  
  Telugu notice: రేషన్ కార్డు తప్ప ప్రత్యేక ఆదాయ/ఆస్తి పరిమితులు మూలాల్లో లేవు.
- **covered_treatments**: Exact list of treatment packages and any sub-limits  
  Telugu notice: ఏఏ చికిత్సలు, ఉప-పరిమితులు ఉన్నాయనే పూర్తి జాబితా నా వద్ద లేదు — ఆరోగ్య మిత్ర లేదా ఆసుపత్రిలో అడగండి.
- **current_hospital_service**: Whether all empanelled private hospitals currently accept Aarogyasri  
  Telugu notice: ప్రస్తుతం అన్ని ప్రైవేట్ ఆసుపత్రులు ఆరోగ్యశ్రీ తీసుకుంటున్నాయో లేదో మూలాల్లో లేదు.

**How to apply:** Show the white ration card (and Aadhaar) at an empanelled hospital; the Aarogya Mithra verifies eligibility. Exact current procedure to be confirmed at the hospital.  

**Sources used:**
- `dc-budget-2526-aarogyasri`: Telangana Budget 2025-26 live (Deccan Chronicle, 2025-03-19) [major_news] <https://deccanchronicle.com/buzz/live-telangana-budget-2025-26-to-be-presented-in-assembly-on-wednesday-1458>
- `ditto-aarogyasri`: Rajiv Aarogyasri: eligibility, coverage, application (Ditto Insurance, 2026-07) [secondary] <https://joinditto.in/articles/health-insurance/rajiv-aarogyasri/>
- `sakshi-aarogyasri-orphans`: Telangana extends Aarogyasri to orphans (Sakshi Post, 2025-05) [major_news] <https://www.sakshipost.com/news/telangana/telangana-extends-aarogyasri-orphans-andhra-grapples-systemic-collapse-408922>
- `sf-aarogyasri-2025`: As talks fail, Telangana private hospitals to suspend Aarogyasri services over pending dues (The South First, 2025-09-17) [major_news] <https://thesouthfirst.com/news/as-talks-fail-telangana-private-hospitals-to-suspend-aarogyasri-services-over-pending-dues>
- `sf-mahalakshmi-launch`: Congress govt in Telangana flags off Mahalakshmi scheme (The South First, 2023-12-09) [major_news] <https://thesouthfirst.com/topstory/congress-govt-in-telangana-flags-off-mahalakshmi-scheme-offering-women-free-rides-on-state-run-buses/>

---

## Indiramma Indlu (housing)

**Telugu name:** ఇందిరమ్మ ఇల్లు  
**scheme_id:** `indiramma_indlu`  
**Status:** `active`  
**Last verified:** 2026-10-28

> Verified by your own verification pass on 22 Oct 2026 against district and state government pages; carried over here.

**Summary:** Financial assistance of Rs 5 lakh for eligible landless and homeless families (and landowners without a permanent house) to build a permanent house. Families who already own a permanent house are not eligible for fresh sanction.

**సారాంశం:** ఇల్లు లేని అర్హ కుటుంబాలకు (భూమి ఉండి శాశ్వత ఇల్లు లేనివారికి, భూమి కూడా లేనివారికి) శాశ్వత ఇల్లు కట్టుకోవడానికి రూ. 5 లక్షల ఆర్థిక సహాయం. ఇప్పటికే శాశ్వత ఇల్లు ఉన్నవారికి కొత్తగా మంజూరు ఉండదు.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| what | Housing initiative giving financial assistance to eligible landless and homeless families in Telangana to construct permanent houses on their own plots. | high | indiramma-indlu-summary, indiramma-portal |
| amount | Assistance is Rs 5 lakh per eligible family. | high | indiramma-indlu-summary, indiramma-mulugu |
| subsidy_wording | The Wanaparthy page uses the wording '100% subsidy'; the state portal does not state this percentage, so treat it as the district page's description and not a universal cost guarantee. | medium | indiramma-indlu-summary, indiramma-portal |
| plot | Landless beneficiaries MAY receive a 250 sq yd residential plot; this is conditional, not an unconditional entitlement. The state portal states no plot size. | medium | indiramma-indlu-summary, indiramma-mulugu |
| l1_l2_l3 | Mulugu district page (7 Aug 2025): L1 = owns a small piece of land but no permanent house; L2 = highly prioritised homeless families owning neither land nor house, may receive a free 250 sq yd plot; L3 = already owns a permanent house, ineligible for new sanction. | high | indiramma-mulugu |
| monitoring | Officials monitor construction through a mobile app with geocoordinates and stage-wise progress. | high | indiramma-indlu-summary, indiramma-portal |
| portal | Application/information portal: https://indirammaindlu.telangana.gov.in/ | high | indiramma-indlu-summary, indiramma-portal |
| date_caveat | The 20 Dec 2023 date on the Wanaparthy page is page metadata, not the scheme launch date. | high | indiramma-indlu-summary |

### Eligibility criteria (ask in this order)

1. **owns_house** — type `yes_no`, required `no`, confidence `high`, source `indiramma-indlu-summary`
   - Question: మీ కుటుంబానికి ఇప్పుడు సొంత ఇల్లు ఉందా?
   - Basis: The Telangana Indiramma Indlu Scheme is a housing initiative that provides financial assistance to eligible, landless, and homeless families in Telangana to construct permanent houses on their own plots.
   - If not met: ఇందిరమ్మ ఇల్లు పథకం ఇప్పుడు సొంత ఇల్లు లేని (homeless) కుటుంబాల కోసం మాత్రమే ఉద్దేశించినది.
2. **telangana_family** — type `yes_no`, required `yes`, confidence `high`, source `indiramma-indlu-summary`
   - Question: మీ కుటుంబం తెలంగాణలోనే నివసిస్తుందా?
   - Basis: The Telangana Indiramma Indlu Scheme is a housing initiative that provides financial assistance to eligible, landless, and homeless families in Telangana to construct permanent houses on their own plots.
   - If not met: ఈ పథకం తెలంగాణలో నివసించే కుటుంబాల కోసం మాత్రమే ఉద్దేశించినది.

### Not covered by sources (say once, then point to the official office)

- **parent_land**: Whether land owned by parents (for example, a father's land) affects the applicant's eligibility  
  Telugu notice: తల్లిదండ్రుల పేరిట ఉన్న భూమి అర్హతను ఏమాత్రం ప్రభావితం చేస్తుందో ప్రచురించిన మూలాల్లో పేర్కొనలేదు — అధికారిక పోర్టల్‌లో ధృవీకరించుకోవాలి.
- **joint_family**: Whether a separate household (living apart from the parents' house) affects eligibility  
  Telugu notice: కలిసి ఉండటం లేదా విడిపోయి ఉండటం అర్హతపై ఎలా ప్రభావం చూపుతుందో మూలాల్లో పేర్కొనలేదు — అధికారిక పోర్టల్‌లో ధృవీకరించుకోవాలి.
- **category_quota**: SC/ST/BC or other category-based quotas, reservations, or priority lists  
  Telugu notice: SC/ST/BC వంటి వర్గాలకు రిజర్వేషన్లు లేదా కోటాల గురించి ప్రచురించిన మూలాల్లో పేర్కొనలేదు — అధికారిక పోర్టల్‌లో ధృవీకరించుకోవాలి.
- **income_limit**: Any income ceiling or asset/wealth criteria for beneficiaries  
  Telugu notice: ఆదాయం లేదా ఆస్తి పరిమితుల గురించి ప్రచురించిన మూలాల్లో పేర్కొనలేదు — అధికారిక పోర్టల్‌లో ధృవీకరించుకోవాలి.
- **document_list**: The list of documents required to apply  
  Telugu notice: దరఖాస్తుకు కావాల్సిన ఆధారాల జాబితా ప్రచురించిన మూలాల్లో ఇంకా లేదు — అధికారిక పోర్టల్‌లో చూడండి.
- **go_citation**: Government order number/title for the scheme  
  Telugu notice: ఈ పథకం ప్రభుత్వ ఉత్తర్వు (GO) సంఖ్య మూలాల్లో లేదు.

**How to apply:** Via the state portal https://indirammaindlu.telangana.gov.in/ . Document list not in sources.  
**Portal:** https://indirammaindlu.telangana.gov.in/  

**Sources used:**
- `indiramma-indlu-summary`: Wanaparthy District: Indiramma Indlu Scheme (Wanaparthy District, Govt of Telangana) [official] <https://wanaparthy.telangana.gov.in/scheme/indiramma-indlu-scheme/>
- `indiramma-mulugu`: Mulugu District: Indiramma Indlu (Mulugu District, Govt of Telangana) [official] <https://mulugu.telangana.gov.in/scheme/indiramma-indlu/>
- `indiramma-portal`: Indiramma Indlu state portal (Govt of Telangana) [official] <https://indirammaindlu.telangana.gov.in/>

---

## Rythu Bharosa (farmer investment support)

**Telugu name:** రైతు భరోసా  
**scheme_id:** `rythu_bharosa`  
**Status:** `active`  
**Last verified:** 2026-10-28

> Carried over from your verification file (checked 22 Oct 2026, Wanaparthy district page last updated 26 Sep 2025). Operational flows (apply, status, check amount) were NOT confirmed on the official portal and are excluded.

**Summary:** Income support of Rs 6,000 per acre per crop season (Rs 12,000 per acre a year for Rabi and Kharif) by DBT to small/marginal farmers, tenant farmers and agricultural labourers on agriculturally suitable land.

**సారాంశం:** చిన్న/స్వల్ప రైతులు, కౌలు రైతులు, వ్యవసాయ కూలీలకు వ్యవసాయ యోగ్యమైన భూమికి ఎకరాకు ప్రతి పంట కాలానికి రూ. 6,000 (రబీ, ఖరీఫ్ కలిపి ఏడాదికి రూ. 12,000) నేరుగా బ్యాంకు ఖాతాలో జమ.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| amount | Rs 6,000 per acre per crop season; Rs 12,000 per acre annually for Rabi and Kharif. *(No GO page cited: the GO PDF was a scanned image.)* | high | rythu-bharosa-wanaparthy-summary |
| dbt | Payment is by DBT into registered bank accounts, in phases during crop seasons. | high | rythu-bharosa-wanaparthy-summary |
| who | Tenant farmers and agricultural labourers are covered, along with small/marginal farmers. | high | rythu-bharosa-wanaparthy-summary |
| exclusions | Mining, industrial and real-estate land is excluded; only agriculturally suitable land qualifies. | high | rythu-bharosa-wanaparthy-summary |
| documents | Aadhaar, land/lease proof, bank passbook, ration card, domicile proof, mobile number and PAN are listed as required documents. | high | rythu-bharosa-wanaparthy-summary |
| blanket_claim_contradicted | The sentence 'all farmers residing in Telangana and owning lands are eligible' is contradicted by the detailed eligibility section and must not be used. | high | rythu-bharosa-wanaparthy-summary |
| portal | Official portal: https://rythubharosa.telangana.gov.in/ | high | rythu-bharosa-portal |

### Eligibility criteria (ask in this order)

1. **telangana_resident** — type `yes_no`, required `yes`, confidence `high`, source `rythu-bharosa-wanaparthy-summary`
   - Question: మీరు తెలంగాణలోనే నివసిస్తున్నారా?
   - Basis: To qualify for the Telangana Rythu Bharosa Scheme, applicants must meet the following eligibility criteria: Must be a resident of Telangana.
   - If not met: ఈ పథకం తెలంగాణలో నివసించే కుటుంబాల కోసం మాత్రమే ఉద్దేశించినది.
2. **age_18_59** — type `yes_no`, required `yes`, confidence `high`, source `rythu-bharosa-wanaparthy-summary`
   - Question: మీ వయసు 18 నుంచి 59 ఏళ్ల మధ్య ఉందా?
   - Basis: To qualify for the Telangana Rythu Bharosa Scheme, applicants must meet the following eligibility criteria: Be between the ages of 18 and 59.
   - If not met: ప్రచురించిన ప్రమాణాల ప్రకారం అర్హత వయసు 18 నుంచి 59 ఏళ్ల మధ్య ఉన్నవారికి మాత్రమే.
3. **agri_role** — type `list`, required `small_or_marginal_farmer / tenant_farmer / agricultural_labourer`, confidence `high`, source `rythu-bharosa-wanaparthy-summary`
   - Question: వ్యవసాయానికి అనువైన భూమిపై మీ పాత్ర ఏది — చిన్న లేదా స్వల్ప రైతు (సొంత భూమి), కౌలుకు వ్యవసాయం చేసే రైతు, లేదా వ్యవసాయ కూలీ?
   - Basis: To qualify for the Telangana Rythu Bharosa Scheme, applicants must meet the following eligibility criteria: Should be a small or marginal farmer engaged in agriculture; Tenant farmers leasing agricultural land are eligible; Agricultural labourers are eligible; Must own/lease agriculturally suitable lands. Mining areas, industrial zones and real estate lands are excluded.
   - If not met: ఈ పథకం చిన్న/స్వల్ప రైతుల, కౌలు రైతుల, వ్యవసాయ కూలీల కోసం మాత్రమే; గనులు, పరిశ్రమలు, రియల్ ఎస్టేట్ వాడకం ఉన్న భూములు అర్హత పరిధిలో లేవు.

### Not covered by sources (say once, then point to the official office)

- **small_marginal_definition**: Land-size definition of small or marginal farmer used by the scheme  
  Telugu notice: చిన్న/స్వల్ప రైతు అంటే ఏ భూమి పరిమాణం అనే నిర్వచనం మూలంలో పేర్కొనలేదు — అధికారిక పోర్టల్‌లో ధృవీకరించుకోవాలి.
- **landless_labourer_proof**: How landless agricultural labourers prove eligibility and what documents they need  
  Telugu notice: భూమి లేని వ్యవసాయ కూలీలు అర్హతను ఎలా రుజువు చేయాలో మూలాల్లో పేర్కొనలేదు — అధికారిక పోర్టల్‌లో చూడండి.
- **rythu_bandhu_overlap**: Relationship between Rythu Bharosa and the earlier Rythu Bandhu scheme (who gets what)  
  Telugu notice: ఇది పాత రైత్ బంధు పథకంతో ఎలా ముడిపడి ఉందో, ఎవరికి ఏది వర్తిస్తుందో మూలంలో స్పష్టంగా లేదు — అధికారిక పోర్టల్‌లో ధృవీకరించుకోవాలి.
- **apply_and_status_flow**: Online apply, status check and 'check amount' flows (stated on the district page but not confirmed on the official portal)  
  Telugu notice: ఆన్‌లైన్ దరఖాస్తు, స్థితి తనిఖీ విధానాలు అధికారిక పోర్టల్‌లో నిర్ధారణ కాలేదు — పోర్టల్ లేదా గ్రామ పంచాయతీలో చూడండి.

**How to apply:** Details not confirmed on the official portal landing page; see portal.  
**Portal:** https://rythubharosa.telangana.gov.in/  

**Sources used:**
- `rythu-bharosa-portal`: Telangana Rythu Bharosa portal (Govt of Telangana) [official] <https://rythubharosa.telangana.gov.in/>
- `rythu-bharosa-wanaparthy-summary`: Wanaparthy District: Rythu Bharosa Scheme (Wanaparthy District, Govt of Telangana) [official] <https://wanaparthy.telangana.gov.in/scheme/rythu-bharosa-scheme/>

---

## Rythu Bima (farmers' group life insurance, Rs 5 lakh)

**Telugu name:** రైతు బీమా (రూ. 5 లక్షల జీవిత బీమా)  
**scheme_id:** `rythu_bima`  
**Status:** `disputed`  
**Last verified:** 2026-10-28

> Operational status is DISPUTED. Telangana Today (4 Sep and 4 Oct 2026) reports the state had not paid the LIC premium and claims were pending. The government's side was not found. Do not assure users that the cover is currently in force.

**Summary:** Free life insurance of Rs 5 lakh for pattadar farmers aged 18 to 59, paid to the nominee on the farmer's death from any cause; the government pays the premium to LIC. Reports in Sep-Oct 2026 say renewal premium payment is in doubt.

**సారాంశం:** 18 నుంచి 59 ఏళ్ల మధ్య ఉన్న పట్టాదారు రైతు ఏ కారణంతో మరణించినా నామినీకి రూ. 5 లక్షల బీమా; ప్రీమియం ప్రభుత్వమే LICకి చెల్లిస్తుంది. అయితే ఈ ఏడాది ప్రీమియం చెల్లింపుపై సందేహాలున్నట్లు వార్తలు వచ్చాయి.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| benefit | Rs 5 lakh insurance cover to the farmer's nominee on death due to any cause, including natural death. | high | myscheme-rythu-bima, tt-bima-premium-sep2026 |
| premium | The entire premium is paid by the government to LIC; the farmer pays nothing. | high | myscheme-rythu-bima |
| age | Farmers aged 18 to 59 are eligible; a court judgment extract says age is counted as on 15 August of the enrolment year. | high | myscheme-rythu-bima, livelaw-lic-bima |
| pattadar | Enrolled farmers are pattadars (land-owning farmers). | medium | livelaw-lic-bima |
| premium_dispute | Telangana Today reported on 4 Sep 2026 that the state had failed to pay the premium, halting the programme, and on 4 Oct 2026 that the last date to pay LIC was 14 August with premium unpaid and claims pending or returned. *(Single outlet; government response not found. Re-check before stating status.)* | medium | tt-bima-premium-sep2026, tt-bima-claims-oct2026 |

### Eligibility criteria (ask in this order)

1. **telangana_resident_farmer** — type `yes_no`, required `yes`, confidence `high`, source `myscheme-rythu-bima`
   - Question: మీరు తెలంగాణలో వ్యవసాయం చేసే రైతా?
   - Basis: Farmers of Telangana are eligible.
   - If not met: ఈ పథకం తెలంగాణ రైతులకు మాత్రమే.
2. **pattadar** — type `yes_no`, required `yes`, confidence `medium`, source `livelaw-lic-bima`
   - Question: మీ పేరు మీద పట్టాదారు పాస్‌బుక్ ఉందా?
   - Basis: Eligible farmers are pattadars.
   - If not met: ఈ బీమాకు పట్టాదారు రైతు అయి ఉండాలి.
3. **age_18_59** — type `yes_no`, required `yes`, confidence `high`, source `myscheme-rythu-bima`
   - Question: మీ వయసు 18 నుంచి 59 ఏళ్ల మధ్య ఉందా?
   - Basis: Farmers aged 18 to 59 are eligible.
   - If not met: అర్హత వయసు 18 నుంచి 59 ఏళ్ల మధ్య మాత్రమే.

### Not covered by sources (say once, then point to the official office)

- **current_renewal**: Whether the 2026-27 premium has been paid and the cover is in force  
  Telugu notice: ఈ సంవత్సరం ప్రీమియం చెల్లించి బీమా అమలులో ఉందో లేదో నిర్ధారణ లేదు — వ్యవసాయ శాఖ అధికారిని అడగండి.
- **claim_procedure**: Documents and steps for claiming  
  Telugu notice: క్లెయిమ్ చేసే విధానం, అవసరమైన పత్రాల వివరాలు మూలాల్లో లేవు.
- **non_pattadar**: Whether tenant farmers or forest-right (RoFR) patta holders are covered  
  Telugu notice: కౌలు రైతులు లేదా అటవీ హక్కుల పట్టాదారులకు వర్తిస్తుందో మూలాల్లో స్పష్టత లేదు.

**How to apply:** Farmers are enrolled by the agriculture department; no premium. Claim via nominee with documents (details not confirmed).  

**Sources used:**
- `livelaw-lic-bima`: Court judgment extract on Rythu Bima enrolment rules (LiveLaw (PDF)) [major_news] <https://livelaw.in/pdf_upload/lic-548122.pdf>
- `myscheme-rythu-bima`: Rythu Bima Scheme (MyScheme (Govt of India portal)) [official] <https://myscheme.gov.in/schemes/rythu-bima>
- `tt-bima-claims-oct2026`: Rythu Bima claims pile up as government leaves farmers' families waiting (Telangana Today, 2026-10-04) [major_news] <https://telanganatoday.com/rythu-bima-claims-pile-up-as-government-leaves-farmers-families-waiting>
- `tt-bima-premium-sep2026`: Telangana farmers anxious as Congress govt fails to pay premium under Rythu Bima (Telangana Today, 2026-09-04) [major_news] <https://telanganatoday.com/telangana-farmers-anxious-as-congress-govt-fails-to-pay-premium-under-rythu-bima>

---

## Rythu Runa Mafi (crop loan waiver up to Rs 2 lakh)

**Telugu name:** రైతు రుణమాఫీ (రూ. 2 లక్షల వరకు)  
**scheme_id:** `rythu_runa_mafi`  
**Status:** `completed_one_time`  
**Last verified:** 2026-10-28

> One-time waiver implemented in phases in July-August 2024. No open application window was found. Disputes about farmers left out continue.

**Summary:** Short-term crop loans taken between 12 Dec 2018 and 9 Dec 2023 were waived up to Rs 2 lakh per family (principal plus interest), with a ration card required for the family. The government says 22.37 lakh farmers got Rs 17,934 crore; the opposition says many were excluded.

**సారాంశం:** 2018 డిసెంబర్ 12 నుంచి 2023 డిసెంబర్ 9 మధ్య తీసుకున్న స్వల్పకాలిక పంట రుణాలు కుటుంబానికి రూ. 2 లక్షల వరకు మాఫీ చేశారు. ఇది ఒకసారి అమలైన పథకం.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| cabinet | Cabinet approved waiving crop loans up to Rs 2 lakh per farmer for loans taken between 12 December 2018 and 9 December 2023. | high | dc-runamafi-cabinet, air-runamafi-go |
| guidelines | Guidelines (July 2024): ceiling Rs 2 lakh per family including principal and interest; short-term loans from scheduled commercial banks, RRBs and DCCBs; waived bottom-up; ration card mandatory; not applicable to SHG, JLG, Rythu Mitra Groups, LECs or rescheduled loans. | high | sf-runamafi-guidelines, air-runamafi-go |
| phases | The remaining waiver up to Rs 2 lakh was released on 15 August 2024 as the third phase. | high | sf-runamafi-ground |
| govt_claim | The government claimed it waived Rs 2 lakh crop loans of 22.37 lakh farmers at a cost of Rs 17,934 crore; the BRS said lakhs were left out. *(Government claim vs opposition claim; present as claims.)* | medium | sf-one-year-govt |

### Eligibility criteria (ask in this order)

1. **loan_period** — type `yes_no`, required `yes`, confidence `high`, source `dc-runamafi-cabinet`
   - Question: మీరు 2018 డిసెంబర్ 12 నుంచి 2023 డిసెంబర్ 9 మధ్య పంట రుణం తీసుకున్నారా?
   - Basis: Loans taken between 12 Dec 2018 and 9 Dec 2023.
   - If not met: ఈ కాలంలో తీసుకున్న రుణాలకే మాఫీ వర్తించింది.
2. **loan_type** — type `yes_no`, required `yes`, confidence `high`, source `air-runamafi-go`
   - Question: ఆ రుణం షెడ్యూల్డ్ వాణిజ్య బ్యాంకు, గ్రామీణ బ్యాంకు లేదా జిల్లా సహకార బ్యాంకు నుంచి తీసుకున్న స్వల్పకాలిక పంట రుణమా?
   - Basis: Short-term loans from scheduled commercial banks, RRBs and DCCBs.
   - If not met: దీర్ఘకాలిక, రీషెడ్యూల్ చేసిన లేదా సంఘాల (SHG/JLG) రుణాలకు మాఫీ వర్తించదు.
3. **ration_card** — type `yes_no`, required `yes`, confidence `high`, source `sf-runamafi-guidelines`
   - Question: మీ కుటుంబానికి రేషన్ కార్డు ఉందా?
   - Basis: Ration card was made mandatory for the family to avail the waiver.
   - If not met: మాఫీకి కుటుంబానికి రేషన్ కార్డు తప్పనిసరి చేశారు.

### Not covered by sources (say once, then point to the official office)

- **new_applications**: Whether any new or appeal applications are accepted in 2026  
  Telugu notice: ఇప్పుడు కొత్త దరఖాస్తులు లేదా అభ్యంతరాల స్వీకరణ ఉందో లేదో మూలాల్లో లేదు — బ్యాంకు/వ్యవసాయ అధికారిని అడగండి.
- **left_out_remedy**: Grievance process for farmers who say they were left out  
  Telugu notice: మాఫీ రాలేదని భావించే రైతులకు ఫిర్యాదు విధానం మూలాల్లో స్పష్టంగా లేదు.

**How to apply:** Closed one-time exercise; use the bank or agriculture department for grievances.  

**Sources used:**
- `air-runamafi-go`: Telangana government issued GO listing guidelines for crop loan waiver (All India Radio News, 2024-07-16) [public_broadcaster] <https://newsonair.gov.in/telangana-government-issued-go-listing-out-guidelines-for-implementation-of-crop-loan-waiver>
- `dc-runamafi-cabinet`: Telangana Cabinet okays Rs 2 lakh crop loan waiver (Deccan Chronicle, 2024-06-22) [major_news] <https://deccanchronicle.com/telangana-cabinet-okays-rs-2-lakh-crop-loan-waiver-with-rs-31000-cr-spend>
- `sf-one-year-govt`: Unfulfilled promises, discontent, graft charges as Congress set to celebrate one year of governance (The South First, 2024-12) [major_news] <https://thesouthfirst.com/news/unfulfilled-promises-discontent-graft-charges-as-congress-set-to-celebrate-one-year-of-governance-in-telangana>
- `sf-runamafi-ground`: Ground report: the wait for loan waiver is agonising for several Telangana farmers (The South First, 2024-08) [major_news] <https://thesouthfirst.com/news/elusive-loan-waiver-the-wait-is-agonising-for-several-telangana-farmers-even-in-cms-home-turf>
- `sf-runamafi-guidelines`: With ration card rider, Telangana government releases guidelines on Rs 2 lakh crop loan waiver (The South First, 2024-07-15) [major_news] <https://thesouthfirst.com/news/with-ration-card-rider-telangana-government-releases-guidelines-on-₹2-lakh-crop-loan-waiver>

---

## Cheyutha (Aasara) social security pensions

**Telugu name:** చేయూత (ఆసరా) పింఛన్లు  
**scheme_id:** `cheyutha_aasara_pensions`  
**Status:** `active_amount_hike_not_implemented`  
**Last verified:** 2026-10-28

> The promised Rs 4,000 old-age pension had not been implemented as of 1 Oct 2026 per Telangana Today (via a secondary summary). Current rates: Rs 2,016 for most categories, Rs 4,016 for disability. Sources disagree on some details; see facts.

**Summary:** Monthly pension of Rs 2,016 for old age (57+), widows and other listed categories, and Rs 4,016 for persons with disabilities. The Rs 4,000 promise is not yet implemented.

**సారాంశం:** వృద్ధాప్య (57 ఏళ్లు పైబడినవారు), వితంతు మరియు ఇతర వర్గాలకు నెలకు రూ. 2,016, దివ్యాంగులకు రూ. 4,016. రూ. 4,000 హామీ ఇంకా అమలు కాలేదు.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| rates | Published monthly rates: old age Rs 2,016, widow Rs 2,016, disability Rs 4,016. | medium | cheyutha-report-oct2026, schemeshelper-cheyutha, ditto-aasara |
| hike_not_done | The proposed increase of the old-age pension from Rs 2,016 to Rs 4,000 was reported as not implemented as of 1 October 2026. *(Secondary summary of a Telangana Today report; verify before stating as final.)* | medium | cheyutha-report-oct2026 |
| promise | A Rs 4,000 monthly pension is among the promises criticised as unfulfilled by the opposition. | medium | sf-guarantees-hindu-ktr |
| age_57 | Old-age pension eligibility starts at 57 years in several explainers (earlier 65). *(Confirm with the local MPDO/municipal office.)* | medium | ditto-aasara |
| disability | Persons with disabilities: no minimum age, SADAREM-certified disability of 40% or more (51% for hearing impairment) per one explainer. | medium | ditto-aasara |
| categories | Categories reported: old age, widows, single women, weavers, toddy tappers, beedi workers, HIV/AIDS and filaria patients, persons with disabilities. | medium | ditto-aasara, schemeshelper-cheyutha |
| conflicting_reports | Some older/low-quality reports claim the Rs 4,000 and Rs 6,000 amounts were already paid; this conflicts with the 1 Oct 2026 report and is not used. | low | cheyutha-report-oct2026 |

### Eligibility criteria (ask in this order)

1. **telangana_resident** — type `yes_no`, required `yes`, confidence `medium`, source `ditto-aasara`
   - Question: మీరు తెలంగాణలో నివసిస్తున్నారా?
   - Basis: Applicants must be Telangana residents.
   - If not met: ఈ పింఛన్లు తెలంగాణ నివాసులకు మాత్రమే.
2. **category** — type `list`, required `old_age / widow / single_woman / weaver / toddy_tapper / beedi_worker / hiv_aids / filaria / disabled`, confidence `medium`, source `ditto-aasara`
   - Question: మీరు ఏ వర్గానికి చెందుతారు — వృద్ధులు, వితంతువు, ఒంటరి మహిళ, నేత కార్మికులు, గీత కార్మికులు, బీడీ కార్మికులు, HIV/ఫైలేరియా బాధితులు, లేదా దివ్యాంగులు?
   - Basis: Pension is for notified categories only.
   - If not met: ఈ పింఛన్లు నిర్దేశిత వర్గాలకు మాత్రమే.
3. **old_age_57_plus** _(applies if category == old_age)_ — type `yes_no`, required `yes`, confidence `medium`, source `ditto-aasara`
   - Question: మీ వయసు 57 ఏళ్లు లేదా అంతకంటే ఎక్కువా?
   - Basis: Old-age pension eligibility reported as 57 years and above.
   - If not met: వృద్ధాప్య పింఛన్‌కు 57 ఏళ్లు నిండి ఉండాలని నివేదికలు చెబుతున్నాయి.
4. **disability_40_plus** _(applies if category == disabled)_ — type `yes_no`, required `yes`, confidence `medium`, source `ditto-aasara`
   - Question: మీకు సదరం ధృవీకరణతో 40% లేదా అంతకంటే ఎక్కువ వైకల్యం ఉందా?
   - Basis: SADAREM-certified disability of 40% or more (51% for hearing impairment).
   - If not met: దివ్యాంగ పింఛన్‌కు సదరం ధృవీకరణతో నిర్దేశిత శాతం వైకల్యం ఉండాలి.

### Not covered by sources (say once, then point to the official office)

- **income_asset_criteria**: Exact income and asset screening/exclusion criteria  
  Telugu notice: ఆదాయ, ఆస్తి పరిమితులపై ఖచ్చితమైన నిబంధనలు మూలాల్లో నిర్ధారణ కాలేదు — MPDO/మున్సిపల్ కార్యాలయంలో అడగండి.
- **other_pension_rule**: Whether a person already receiving another pension is excluded  
  Telugu notice: మరో పింఛన్ పొందుతున్నవారికి నియమం మూలాల్లో నిర్ధారణ కాలేదు.
- **hike_timeline**: When or whether the Rs 4,000 pension will start  
  Telugu notice: రూ. 4,000 పింఛన్ ఎప్పుడు ప్రారంభమవుతుందో తెలియదు.
- **application_window**: How and when new applicants can apply  
  Telugu notice: కొత్తగా ఎప్పుడు, ఎలా దరఖాస్తు చేయాలనే వివరాలు మూలాల్లో నిర్ధారణ కాలేదు.

**How to apply:** Offline via Gram Panchayat / municipal office per explainers; status via the Cheyutha (SSPTG) portal. Not confirmed from an official page in this pass.  

**Sources used:**
- `cheyutha-report-oct2026`: Cheyutha Pension Payment Status and Latest Updates (cites Telangana Today, 1 Oct 2026) (cheyuthapension.in, 2026-10) [secondary] <https://cheyuthapension.in/cheyutha-pension-payment-status/>
- `ditto-aasara`: Aasara Pension Scheme Telangana: eligibility and amount (Ditto Insurance, 2026-09) [secondary] <https://joinditto.in/articles/general/aasara-pension-scheme/>
- `schemeshelper-cheyutha`: Cheyutha Pension Telangana 2026 (SchemesHelper, 2026-09) [secondary] <https://schemeshelper.com/cheyutha-pension-telangana/>
- `sf-guarantees-hindu-ktr`: KTR says Revanth made Rahul lie about promises (The Hindu via PressReader) (The Hindu, 2024-05-06) [major_news] <https://www.pressreader.com/india/the-hindu-international-9BN2/20240506/281651080189161>

---

## Kalyana Lakshmi / Shaadi Mubarak (marriage assistance)

**Telugu name:** కళ్యాణలక్ష్మి / షాదీ ముబారక్  
**scheme_id:** `kalyana_lakshmi_shaadi_mubarak`  
**Status:** `active`  
**Last verified:** 2026-10-28

> Running since 2 Oct 2014. The promised gold (tula) addition was not found in any reputable report; a viral video claiming it was confirmed a deepfake in Oct 2026.

**Summary:** One-time marriage assistance of Rs 1,00,116 for brides aged 18 or more from eligible families (Kalyana Lakshmi for SC/ST/BC/EBC, Shaadi Mubarak for minorities), with parents' combined annual income up to Rs 2 lakh.

**సారాంశం:** 18 ఏళ్లు నిండిన అర్హ వధువులకు వివాహ సమయంలో ఒకసారి రూ. 1,00,116 సహాయం (SC/ST/BC/EBC లకు కళ్యాణలక్ష్మి, మైనారిటీలకు షాదీ ముబారక్). తల్లిదండ్రుల మొత్తం వార్షిక ఆదాయం రూ. 2 లక్షల లోపు ఉండాలి.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| launch | Launched on 2 October 2014 to support marriage expenses and discourage child marriage; assistance is conditional on the bride being at least 18. | high | tt-kl-12years, cgg-kl |
| amount | Assistance is Rs 1,00,116 per bride. *(Amount repeated by many explainers; confirm on ePASS.)* | medium | housing-kl, tt-kl-12years |
| disabled | Parents of disabled girls get Rs 1,25,145 under the Shaadi Mubarak listing on the national MyScheme portal. | high | myscheme-sms |
| income | The combined annual income of the bride's parents should be less than Rs 2 lakh. | high | myscheme-sms |
| one_time | It is one-time assistance, available only once in a lifetime. | high | myscheme-sms |
| unmarried | The scheme is for unmarried girls aged 18 or more. | high | myscheme-sms |
| how | Applicants apply online through the Telangana ePASS website under Kalyana Lakshmi / Shaadi Mubarak. | high | myscheme-sms |
| beneficiaries | 16.78 lakh beneficiaries by October 2026. | high | tt-kl-12years |
| gold_not_added | No reputable report found that gold has been added to the assistance; a viral video claiming this was reported as a deepfake on 8 Oct 2026. | medium | oneindia-deepfake-2500 |

### Eligibility criteria (ask in this order)

1. **telangana_resident** — type `yes_no`, required `yes`, confidence `high`, source `myscheme-sms`
   - Question: వధువు తెలంగాణ నివాసి నా?
   - Basis: Scheme is for residents of Telangana.
   - If not met: ఈ పథకం తెలంగాణ నివాసులకు మాత్రమే.
2. **bride_18_plus_unmarried** — type `yes_no`, required `yes`, confidence `high`, source `myscheme-sms`
   - Question: వధువు వయసు 18 ఏళ్లు లేదా అంతకంటే ఎక్కువా, మరియు ఇది ఆమె మొదటి వివాహమా?
   - Basis: Unmarried girls aged 18 or more.
   - If not met: వధువుకు వివాహ సమయానికి 18 ఏళ్లు నిండి ఉండాలి.
3. **community** — type `list`, required `sc / st / bc / ebc / minority`, confidence `medium`, source `cgg-kl`
   - Question: వధువు SC, ST, BC, EBC లేదా మైనారిటీ వర్గానికి చెందినవారా?
   - Basis: Kalyana Lakshmi for SC/ST (later BC/EBC); Shaadi Mubarak for minorities.
   - If not met: ఈ పథకం నిర్దేశిత వర్గాలకు మాత్రమే.
4. **parents_income_under_2_lakh** — type `yes_no`, required `yes`, confidence `high`, source `myscheme-sms`
   - Question: వధువు తల్లిదండ్రుల మొత్తం వార్షిక ఆదాయం రూ. 2 లక్షల లోపేనా?
   - Basis: Combined annual income of parents less than Rs 2 lakh.
   - If not met: తల్లిదండ్రుల మొత్తం వార్షిక ఆదాయం రూ. 2 లక్షల లోపు ఉండాలి.

### Not covered by sources (say once, then point to the official office)

- **bc_rural_limit**: Whether a lower income limit (Rs 1.5 lakh) applies to rural BC/EBC applicants (one explainer says so)  
  Telugu notice: గ్రామీణ BC/EBC లకు ఆదాయ పరిమితి రూ. 1.5 లక్షలా అనే విషయం ఒక్క మూలంలోనే ఉంది — ePASS లో నిర్ధారించుకోండి.
- **application_deadline**: Time limit to apply before or after marriage  
  Telugu notice: వివాహానికి ముందు/తర్వాత ఎంత గడువులోపు దరఖాస్తు చేయాలనేది మూలాల్లో నిర్ధారణ కాలేదు.
- **gold_promise**: Whether the manifesto promise of gold has been implemented  
  Telugu notice: కళ్యాణలక్ష్మి కింద బంగారం హామీ అమలైనట్లు నమ్మదగిన మూలాల్లో లేదు.

**How to apply:** Online through Telangana ePASS (telanganaepass.cgg.gov.in) under Kalyana Lakshmi / Shaadi Mubarak.  
**Portal:** https://telanganaepass.cgg.gov.in/  

**Sources used:**
- `cgg-kl`: Kalyana Lakshmi - Shaadi Mubarak (CGG, Govt of Telangana) [official] <https://www.cgg.gov.in/it_project/kalyana-lakshmi-shaadi-mubarak/>
- `housing-kl`: Kalyana Lakshmi scheme: documents, eligibility and key details (Housing.com) [secondary] <https://housing.com/news/kalyana-lakshm-scheme>
- `myscheme-sms`: Shaadi Mubarak Scheme (MyScheme (Govt of India portal)) [official] <https://myscheme.gov.in/hi/schemes/sms>
- `oneindia-deepfake-2500`: Revanth Reddy Rs 2,500 aid / 2 tulas gold video confirmed deepfake (Oneindia Telugu, 2026-10-08) [major_news] <https://telugu.oneindia.com/news/telangana/cm-revanth-reddy-on-rs-2-500-aid-for-women-2tulas-gold-in-kalyana-lakshmi-from-bathukamma-deepfake-509703.html>
- `tt-kl-12years`: Kalyana Lakshmi, Shaadi Mubarak complete 12 years with 16.78 lakh beneficiaries (Telangana Today, 2026-10-01) [major_news] <https://telanganatoday.com/kalyana-lakshmi-shaadi-mubarak-complete-12-years-with-16-78-lakh-beneficiaries>

---

## Rajiv Yuva Vikasam (self-employment subsidy for youth)

**Telugu name:** రాజీవ్ యువ వికాసం  
**scheme_id:** `rajiv_yuva_vikasam`  
**Status:** `active_implementation_unclear`  
**Last verified:** 2026-10-28

> Launched 17 Mar 2025. About 16.25 lakh applications received; sources conflict on subsidy slabs and age limits, and implementation progress is unclear.

**Summary:** Bank-linked subsidy for unemployed youth from SC, ST, BC, EBC and minority communities to start self-employment units, reported as up to Rs 3-4 lakh. Slabs reported differ between sources.

**సారాంశం:** SC, ST, BC, EBC, మైనారిటీ వర్గాల నిరుద్యోగ యువతకు స్వయం ఉపాధి యూనిట్లు ప్రారంభించడానికి బ్యాంకు రుణంతో కలిపి సబ్సిడీ (రూ. 3–4 లక్షల వరకు అని నివేదికలు). సబ్సిడీ శ్లాబులపై మూలాలు ఒకేలా లేవు.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| launch | The Chief Minister launched Rajiv Yuva Vikasam on 17 March 2025. | high | air-ryv-launch |
| what | Young people can receive concessional loans of up to Rs 4 lakh along with subsidies to set up businesses or self-employment units. | high | cgg-ryv |
| income | Income limit reported as Rs 1.5 lakh per year in rural areas and Rs 2 lakh in urban areas. | high | dc-ryv-cibil, siasat-ryv-slabs |
| age | Age limit reported as 21 to 60 for rural and 21 to 55 for urban applicants by one outlet; another explainer says 21-55 (21-60 for agriculture units). *(Conflicting; do not state a single age band as certain.)* | medium | dc-ryv-cibil |
| slabs_conflict | Subsidy slab reports differ: one lists 100% up to Rs 50,000, 90% up to Rs 1 lakh, 80% up to Rs 2 lakh, 70% up to Rs 4 lakh; another says 80% to Rs 1 lakh, 70% to Rs 2 lakh and 60% to Rs 3 lakh; another says 60% for Rs 3-4 lakh. *(Do not quote a slab to users until verified on the official portal.)* | low | siasat-ryv-slabs, adda-ryv, siasat-ryv-cibil |
| applications | About 16.25 lakh people applied and a large share were expected to be rejected. | medium | siasat-ryv-cibil |
| cibil | Reports say a CIBIL score requirement applies for the bank-linked part. | medium | siasat-ryv-cibil, dc-ryv-cibil |

### Eligibility criteria (ask in this order)

1. **telangana_resident** — type `yes_no`, required `yes`, confidence `high`, source `cgg-ryv`
   - Question: మీరు తెలంగాణలో నివసిస్తున్నారా?
   - Basis: Scheme is for young people of Telangana.
   - If not met: ఈ పథకం తెలంగాణ యువతకు మాత్రమే.
2. **unemployed** — type `yes_no`, required `yes`, confidence `medium`, source `air-ryv-launch`
   - Question: మీరు ప్రస్తుతం నిరుద్యోగులా?
   - Basis: Scheme supports unemployed youth in self-employment.
   - If not met: ఈ పథకం నిరుద్యోగ యువతకు ఉద్దేశించినది.
3. **community** — type `list`, required `sc / st / bc / ebc / minority`, confidence `medium`, source `siasat-ryv-slabs`
   - Question: మీరు SC, ST, BC, EBC లేదా మైనారిటీ వర్గానికి చెందినవారా?
   - Basis: Reported target communities.
   - If not met: ఈ పథకం నిర్దేశిత వర్గాల యువతకు మాత్రమే అని నివేదికలు చెబుతున్నాయి.
4. **family_income** — type `yes_no`, required `yes`, confidence `high`, source `dc-ryv-cibil`
   - Question: మీ కుటుంబ వార్షిక ఆదాయం గ్రామీణ ప్రాంతంలో రూ. 1.5 లక్షలు లేదా పట్టణ ప్రాంతంలో రూ. 2 లక్షల లోపేనా?
   - Basis: Income Rs 1.5 lakh (rural) and Rs 2 lakh (urban).
   - If not met: కుటుంబ ఆదాయ పరిమితి గ్రామీణంలో రూ. 1.5 లక్షలు, పట్టణంలో రూ. 2 లక్షలు.

### Not covered by sources (say once, then point to the official office)

- **age_band**: Exact age band (21-55 vs 21-60 for rural/agriculture)  
  Telugu notice: వయో పరిమితిపై మూలాలు ఒకేలా చెప్పడం లేదు (21–55 లేదా 21–60) — అధికారిక పోర్టల్‌లో చూడండి.
- **subsidy_slabs**: Official subsidy percentage for each unit-cost slab  
  Telugu notice: యూనిట్ ఖర్చును బట్టి సబ్సిడీ శాతం మూలాల్లో వేర్వేరుగా ఉంది — అధికారిక పోర్టల్‌లో ధృవీకరించుకోండి.
- **grounding_status**: Whether units have been sanctioned and grounded  
  Telugu notice: యూనిట్ల మంజూరు, అమలు ఎంతవరకు జరిగిందో నిర్ధారణ లేదు.

**How to apply:** Online through the OBMMS portal (tgobmms.cgg.gov.in) per reports; application window may be closed.  
**Portal:** https://tgobmms.cgg.gov.in/  

**Sources used:**
- `adda-ryv`: Telangana government launches Rajiv Yuva Vikasam scheme (Adda247 Current Affairs, 2025) [secondary] <https://currentaffairs.adda247.com/telangana-government-launches-rajiv-yuva-vikasam-scheme-to-boost-self-employment/>
- `air-ryv-launch`: Telangana CM launches Rajiv Yuva Vikasam (All India Radio News, 2025-03-18) [public_broadcaster] <https://www.newsonair.gov.in/telangana-cm-launches-rajiv-yuva-vikasam-to-boost-self-employment-for-youth>
- `cgg-ryv`: Rajiv Yuva Vikasam (CGG, Govt of Telangana) [official] <https://www.cgg.gov.in/it_project/rajiv-yuva-vikasam/>
- `dc-ryv-cibil`: Bhatti's word falls flat: banks insist on CIBIL (Deccan Chronicle, 2025) [major_news] <https://deccanchronicle.com/southern-states/telangana/bhatti-word-falls-flat-banks-insist-on-cibil-1881738>
- `siasat-ryv-cibil`: Telangana: CIBIL score mandatory for Rajiv Yuva Vikasam scheme (Siasat, 2025) [major_news] <https://www.siasat.com/telangana-cibil-score-mandatory-for-rajiv-yuva-vikasam-scheme-3216483/amp/>
- `siasat-ryv-slabs`: Telangana minority youth urged to apply for RYV scheme before April 5 deadline (Siasat, 2025-04) [major_news] <https://www.siasat.com/telangana-minority-youth-urged-to-apply-for-ryv-scheme-before-april-5-deadline-3200684/amp/>

---

## New ration cards and free fine rice (6 kg per person)

**Telugu name:** కొత్త రేషన్ కార్డులు మరియు ఉచిత సన్న బియ్యం (ఒక్కొక్కరికి 6 కిలోలు)  
**scheme_id:** `ration_cards_fine_rice`  
**Status:** `active`  
**Last verified:** 2026-10-28

> A white ration card (food security card) is the gateway to several other schemes (Gruha Jyothi, LPG Rs 500, Aarogyasri, loan waiver).

**Summary:** Eligible families hold food security cards and receive 6 kg of fine rice per person per month free. New card issuance began in 2025 after a long gap.

**సారాంశం:** ఆహార భద్రతా కార్డు ఉన్న అర్హ కుటుంబాలకు ఒక్కొక్కరికి నెలకు 6 కిలోల సన్న బియ్యం ఉచితంగా లభిస్తుంది. 2025లో చాలా ఏళ్ల తర్వాత కొత్త కార్డుల జారీ మొదలైంది.

### Facts

| ID | Claim | Confidence | Sources |
|---|---|---|---|
| fine_rice | 6 kg of fine rice per person per month is given free through fair price shops to about 3.1 crore people (about 84% of the population) at a cost of over Rs 13,000 crore a year (Civil Supplies Minister, July 2025). | high | uni-fine-rice-2025, sf-ration-cards-july2025 |
| new_cards_start | New ration card issuance and name additions began from 26 January 2025; mass distribution of new cards was launched in mid-July 2025 (reports give 13 or 14 July). | high | sf-ration-cards-july2025, uni-fine-rice-2025, siasat-ration-jan2025 |
| names_added | About 17 lakh new names were added to existing cards between February and May 2025, and applications were taken through MeeSeva centres. | high | siasat-ration-17lakh |
| numbers_2026 | As of August 2026 the Civil Supplies Minister said there were 1,06,28,092 food security cards covering 3.43 crore beneficiaries, with 16,32,810 new cards issued since 26 Jan 2025. | high | uni-ration-cards-aug2026 |
| smart_cards | A move to smart ration cards was announced in August 2026. | medium | uni-ration-cards-aug2026 |
| rules_followed | The minister in charge said no new criteria were laid down for new cards and past eligibility rules would be followed. | medium | siasat-ration-jan2025 |

### Eligibility criteria (ask in this order)

1. **telangana_resident** — type `yes_no`, required `yes`, confidence `medium`, source `sf-ration-cards-july2025`
   - Question: మీరు తెలంగాణలో నివసిస్తున్నారా?
   - Basis: Cards are issued to residents of Telangana.
   - If not met: ఈ కార్డులు తెలంగాణ నివాసులకు మాత్రమే.

### Not covered by sources (say once, then point to the official office)

- **income_land_limits**: Exact income and land-holding limits for a food security card (a Dec 2024 report mentions proposed limits of Rs 1.5 lakh rural / Rs 2 lakh urban income and under 3.5 acres dry or 7.5 acres wet land; later statements said past rules apply)  
  Telugu notice: ఆదాయం, భూమి పరిమితులపై తుది నిబంధనలు మూలాల్లో నిర్ధారణ కాలేదు (గ్రామీణంలో రూ. 1.5 లక్షలు, పట్టణంలో రూ. 2 లక్షలు అని ప్రతిపాదనలు వచ్చాయి) — MeeSeva/పౌర సరఫరాల కార్యాలయంలో ధృవీకరించుకోండి.
- **application_process_now**: Current application window and documents  
  Telugu notice: ఇప్పుడు కొత్త కార్డుకు ఎలా దరఖాస్తు చేయాలి, ఏ పత్రాలు కావాలనేది మూలాల్లో నిర్ధారణ కాలేదు.
- **smart_card_timeline**: Smart card rollout schedule  
  Telugu notice: స్మార్ట్ రేషన్ కార్డుల పంపిణీ తేదీలు మూలాల్లో నిర్ధారణ కాలేదు.

**How to apply:** Through MeeSeva centres / civil supplies offices; current procedure not confirmed.  

**Sources used:**
- `sf-ration-cards-july2025`: Telangana CM launches ration card distribution (The South First, 2025-07-13) [major_news] <https://thesouthfirst.com/news/no-bribes-no-brokers-telangana-cm-revanth-launches-ration-card-distribution-to-cover-3-crore-people-in-record-welfare-drive>
- `siasat-ration-17lakh`: Telangana adds 17 lakh new names to ration cards after 8 years (Siasat, 2025-05-13) [major_news] <https://www.siasat.com/telangana-adds-17-lakh-new-names-to-ration-cards-after-8-years-3220027/amp/>
- `siasat-ration-jan2025`: Harish Rao urges Telangana govt to increase income limit for ration card eligibility (Siasat, 2025-01-19) [major_news] <https://www.siasat.com/harish-rao-urges-telangana-govt-to-increase-income-limit-for-ration-card-eligibility-3167304/amp/>
- `uni-fine-rice-2025`: Telangana to begin distributing new ration cards from July 14 (UNI) (UNI India, 2025-07-02) [major_news] <https://www.uniindia.com/news/south/politics-telangana-ration-cards/3505515.html>
- `uni-ration-cards-aug2026`: Telangana smart ration cards / food security card figures (UNI) (UNI India, 2026-08) [major_news] <https://test.uniindia.com/news/south/admin-telangana-smart-ration-cards/3939984.html>

# KSP InvestigateAI — Crime Domain Model

## 1. Entity Types

### Core Entities (15+)

| # | Entity | Description | Key Attributes |
|---|--------|-------------|----------------|
| 1 | **FIR** | First Information Report | firNumber, dateRegistered, sections[], status, summary, psCode, districtCode |
| 2 | **Person** | Any individual (accused, victim, witness, IO) | name, fatherName, age, gender, aadhaar*, phone, address, photo, fingerprint |
| 3 | **Vehicle** | Any vehicle linked to a case | regNumber, chassisNumber, engineNumber, make, model, color, type, ownerName |
| 4 | **Phone** | Phone number entity | number, provider, circle, type(prepaid/postpaid), activationDate |
| 5 | **IMEI** | Device identifier | imeiNumber, make, model, associatedNumbers[] |
| 6 | **UPI** | UPI payment handle | upiId, linkedBank, linkedPhone, linkedName |
| 7 | **BankAccount** | Bank account | accountNumber, ifsc, bankName, branch, holderName, type(savings/current) |
| 8 | **CCTV** | CCTV camera/footage | cameraId, location, owner, resolution, footageStartTime, footageEndTime |
| 9 | **Evidence** | Any piece of evidence | evidenceId, type(physical/digital/documentary), description, collectionDate, chain[] |
| 10 | **Location** | Geographic point/area | lat, lng, address, landmark, type(crime_scene/residence/hideout), geofence |
| 11 | **PoliceStation** | Police station | psCode, psName, districtCode, jurisdiction, sho, contactNumber |
| 12 | **District** | Administrative district | districtCode, districtName, spName, totalPS, population |
| 13 | **CrimeCategory** | Classification of crime | categoryCode, categoryName, ipcSections[], bnsSections[], severity |
| 14 | **Organization** | Company/gang/group | name, type(company/gang/ngo), registrationNumber, members[], address |
| 15 | **Address** | Structured address | doorNumber, street, area, city, district, state, pincode, coordinates |
| 16 | **Weapon** | Weapon involved in crime | weaponType, description, licenseNumber, seizureDetails |
| 17 | **DigitalAccount** | Social media/email | platform, handle/email, profileUrl, associatedPhone |
| 18 | **Property** | Stolen/recovered property | propertyType, description, value, status(stolen/recovered/seized) |

---

## 2. Relationship Types

### Core Relationships (20+)

| # | Relationship | From → To | Properties |
|---|-------------|-----------|------------|
| 1 | **ACCUSED_IN** | Person → FIR | role(main/abettor/conspirator), arrestDate, bailStatus, sectionsApplied[] |
| 2 | **VICTIM_IN** | Person → FIR | injuryType, lossAmount, statement161Date |
| 3 | **WITNESS_IN** | Person → FIR | witnessType(eye/expert/official), statementDate, reliability |
| 4 | **USED_IN** | Vehicle/Phone/Weapon → FIR | usageType(escape/communication/assault), evidenceStrength |
| 5 | **CO_ACCUSED_WITH** | Person → Person | coAccusedIn[], frequency, firstOccurrence, lastOccurrence |
| 6 | **SHARES_PHONE_WITH** | Person → Person | sharedNumber, overlapPeriod, callFrequency |
| 7 | **SHARES_VEHICLE_WITH** | Person → Person | vehicleRegNumber, ownershipType, usagePeriod |
| 8 | **SHARES_UPI_WITH** | Person → Person | sharedUPI, transactionCount, totalAmount |
| 9 | **FINANCIAL_FLOW** | BankAccount/UPI → BankAccount/UPI | amount, timestamp, transactionId, purpose, layer |
| 10 | **TEMPORAL_PROXIMITY** | FIR → FIR | timeDelta, sameDay, withinHours, sequenceOrder |
| 11 | **SAME_MODUS_OPERANDI** | FIR → FIR | similarityScore, matchedAttributes[], confidence |
| 12 | **OCCURRED_AT** | FIR → Location | crimeSceneType, discoveryTime, reportTime |
| 13 | **CATEGORIZED_AS** | FIR → CrimeCategory | primary(bool), confidence |
| 14 | **REGISTERED_AT** | FIR → PoliceStation | registrationDate, registeredBy, zeroFIR(bool) |
| 15 | **BELONGS_TO** | PoliceStation → District | jurisdictionArea, populationServed |
| 16 | **CONTACTED** | Phone → Phone | callCount, smsCount, firstContact, lastContact, totalDuration |
| 17 | **CAPTURED_BY** | Person/Vehicle → CCTV | timestamp, confidence, imageRef, matchType(face/plate/body) |
| 18 | **LINKED_TO** | Evidence → FIR | linkType, relevance, admissibility, collectionOfficer |
| 19 | **SIMILAR_TO** | Person → Person | similarityType(appearance/behavior/alias), confidence |
| 20 | **HOTSPOT** | Location → CrimeCategory | incidentCount, timeRange, riskScore, trend(increasing/decreasing) |
| 21 | **OWNS** | Person → Vehicle/Property/BankAccount | ownershipType, since, verified(bool) |
| 22 | **RESIDES_AT** | Person → Address | residenceType(permanent/temporary), since, verified(bool) |
| 23 | **MEMBER_OF** | Person → Organization | role, joinDate, activeStatus |
| 24 | **INVESTIGATED_BY** | FIR → Person(IO) | assignDate, transferDate, status |
| 25 | **FAMILY_OF** | Person → Person | relation(father/mother/spouse/sibling/child) |

---

## 3. Crime Categories (IPC/BNS Mapping)

| # | Category | IPC Sections | BNS Sections | Severity | Chargesheet Deadline |
|---|----------|-------------|--------------|----------|---------------------|
| 1 | **Theft** | 379, 380, 381, 382 | 303, 304, 305 | Medium | 60 days |
| 2 | **Cybercrime** | 420 + IT Act 66, 66C, 66D | 318 + IT Act | High | 90 days |
| 3 | **Fraud/Cheating** | 420, 406, 415, 418 | 318, 316, 319 | Medium-High | 60 days |
| 4 | **Assault** | 323, 324, 325, 326 | 115, 116, 117, 118 | Medium | 60 days |
| 5 | **Murder** | 302, 304, 304A | 101, 105, 106 | Critical | 90 days |
| 6 | **NDPS** | NDPS Act 15-29 | NDPS Act (unchanged) | High | 180 days |
| 7 | **POCSO** | POCSO Act 3-12 | POCSO Act (unchanged) | Critical | 60 days |
| 8 | **Chain Snatching** | 356 + 379 | 304 + 131 | Medium-High | 60 days |
| 9 | **Vehicle Theft** | 379, 411 | 303, 317 | Medium | 60 days |
| 10 | **Robbery** | 392, 393, 394, 397 | 309, 310 | High | 90 days |
| 11 | **Kidnapping** | 363, 364, 364A, 365 | 137, 138, 139, 140 | Critical | 90 days |
| 12 | **Economic Offence** | 420, 406, 467, 468, 471 | 318, 316, 336, 337, 340 | High | 90 days |
| 13 | **Property Crime** | 425, 426, 427, 435, 436 | 324, 325, 326 | Medium | 60 days |
| 14 | **Sexual Offence** | 354, 376, 509 | 74, 63, 64, 65, 79 | Critical | 60 days |
| 15 | **Organized Crime** | KCOCA / MCOCA | KCOCA (unchanged) | Critical | 180 days |
| 16 | **Arms Act** | Arms Act 25, 27 | Arms Act (unchanged) | High | 60 days |
| 17 | **Domestic Violence** | 498A, DV Act | 84, 85, 86 | High | 60 days |
| 18 | **SC/ST Atrocity** | SC/ST POA Act | SC/ST POA Act (unchanged) | Critical | 60 days |

---

## 4. Modus Operandi Taxonomy

### MO Dimensions

```
MO Descriptor = {
  method: string,        // How the crime is committed
  target: string,        // Who/what is targeted
  timing: string,        // When the crime occurs
  geography: string,     // Where (area type, terrain)
  tool: string,          // Instruments used
  weapon: string,        // Weapons if any
  approach: string,      // How offender approaches victim
  escape: string,        // Exit strategy
  disguise: string,      // Concealment methods
  accomplices: number,   // Solo or group
}
```

### Method Classification

| Crime Type | Methods |
|-----------|---------|
| **Vehicle Theft** | Master key, key duplication, towing, break glass, electronic bypass, exploit keyless |
| **Burglary** | Glass cutting, lock picking, wall breaking, roof entry, duplicate key, exploit absence |
| **Chain Snatching** | Drive-by snatch, pedestrian approach, distraction, razor cut |
| **Cybercrime** | Phishing, vishing, OTP fraud, SIM swap, malware, social engineering, fake app |
| **Fraud** | Ponzi scheme, advance fee, investment, job fraud, matrimonial, lottery, loan app |
| **Robbery** | Armed threat, group intimidation, drugging, home invasion |

### Target Classification

| Dimension | Categories |
|-----------|-----------|
| **Person Type** | Senior citizen, woman alone, tourist, daily wage worker, businessman, student |
| **Vehicle Type** | Two-wheeler (scooter/bike), four-wheeler (sedan/SUV), auto, commercial |
| **Location Type** | Residence, shop, ATM, bank, temple, park, bus stop, isolated road |
| **Time-of-day** | Early morning (5-7), morning (7-10), afternoon (12-3), evening (5-8), night (10-2), late night (2-5) |
| **Day-of-week** | Weekday, weekend, festival day, market day, salary day |

### MO Similarity Scoring

```
similarityScore(mo1, mo2) = weighted_average(
  method_match * 0.30,
  target_match * 0.20,
  timing_match * 0.15,
  geography_match * 0.15,
  tool_match * 0.10,
  approach_match * 0.05,
  escape_match * 0.05
)
```

---

## 5. Karnataka-Specific Configuration

### Districts (30 Districts + Bangalore City)

| # | District Code | District Name | HQ | Major Towns |
|---|--------------|---------------|-----|-------------|
| 1 | BLR-C | Bangalore City | Bangalore | Whitefield, Electronic City, Yelahanka |
| 2 | BLR-R | Bangalore Rural | Bangalore | Devanahalli, Nelamangala, Hosakote |
| 3 | MYS | Mysore | Mysore | Nanjangud, Hunsur, T. Narasipura |
| 4 | BGM | Belgaum (Belagavi) | Belagavi | Gokak, Athani, Chikkodi |
| 5 | DWD | Dharwad | Dharwad | Hubli, Kundgol, Navalgund |
| 6 | GBG | Gulbarga (Kalaburagi) | Kalaburagi | Sedam, Aland, Afzalpur |
| 7 | BDR | Bidar | Bidar | Basavakalyan, Bhalki, Humnabad |
| 8 | RCR | Raichur | Raichur | Sindhanur, Manvi, Lingasugur |
| 9 | BLY | Bellary (Ballari) | Ballari | Hospet, Siruguppa, Sandur |
| 10 | DKN | Dakshina Kannada | Mangalore | Bantwal, Puttur, Sullia |
| 11 | UKN | Udupi | Udupi | Kundapura, Karkala, Brahmavar |
| 12 | SMG | Shimoga (Shivamogga) | Shivamogga | Bhadravati, Sagar, Tirthahalli |
| 13 | CHK | Chikmagalur | Chikmagalur | Kadur, Tarikere, Mudigere |
| 14 | HAS | Hassan | Hassan | Arsikere, Channarayapatna, Holenarasipura |
| 15 | TUM | Tumkur (Tumakuru) | Tumakuru | Tiptur, Madhugiri, Sira |
| 16 | KLR | Kolar | Kolar | KGF, Bangarpet, Malur |
| 17 | CHN | Chitradurga | Chitradurga | Davangere, Challakere, Hiriyur |
| 18 | DVG | Davangere | Davangere | Harihar, Channagiri, Jagalur |
| 19 | HVR | Haveri | Haveri | Ranebennur, Byadgi, Savanur |
| 20 | GTG | Gadag | Gadag | Nargund, Ron, Mundargi |
| 21 | BGR | Bagalkot | Bagalkot | Badami, Jamkhandi, Mudhol |
| 22 | BJP | Bijapur (Vijayapura) | Vijayapura | Basavan Bagewadi, Muddebihal, Indi |
| 23 | KPL | Koppal | Koppal | Gangavathi, Kushtagi, Yelburga |
| 24 | RMN | Ramanagara | Ramanagara | Channapatna, Magadi, Kanakapura |
| 25 | CKB | Chikkaballapur | Chikkaballapur | Gauribidanur, Sidlaghatta, Bagepalli |
| 26 | MDY | Mandya | Mandya | Srirangapatna, Maddur, Nagamangala |
| 27 | CDG | Chamarajanagar | Chamarajanagar | Kollegal, Gundlupet, Yelandur |
| 28 | KDG | Kodagu | Madikeri | Virajpet, Somwarpet |
| 29 | UTK | Uttara Kannada | Karwar | Sirsi, Honnavar, Ankola |
| 30 | YDG | Yadgir | Yadgir | Shorapur, Shahpur |

### Bangalore City — Zone/Division/Station Hierarchy

```
Bangalore City Police
├── East Zone
│   ├── Whitefield Division
│   │   ├── Whitefield PS, Marathahalli PS, Varthur PS, Kadugodi PS
│   ├── KR Puram Division
│   │   ├── KR Puram PS, Ramamurthy Nagar PS, Banaswadi PS
│   ├── Indiranagar Division
│       ├── Indiranagar PS, HAL PS, Ulsoor PS
├── West Zone
│   ├── Rajajinagar Division
│   │   ├── Rajajinagar PS, Basaveshwara Nagar PS, Kamakshipalya PS
│   ├── Magadi Road Division
│       ├── Magadi Road PS, Vijayanagar PS, Kengeri PS
├── South Zone
│   ├── Jayanagar Division
│   │   ├── Jayanagar PS, Tilak Nagar PS, Banashankari PS
│   ├── HSR Layout Division
│   │   ├── HSR PS, Bellandur PS, Koramangala PS
│   ├── JP Nagar Division
│       ├── JP Nagar PS, Kumaraswamy Layout PS
├── North Zone
│   ├── Yelahanka Division
│   │   ├── Yelahanka PS, Jnanabharathi PS, Vidyaranyapura PS
│   ├── Hebbal Division
│       ├── Hebbal PS, RT Nagar PS, Sanjaynagar PS
├── Central Zone
│   ├── High Grounds Division
│   │   ├── High Grounds PS, Cubbon Park PS, Cottonpet PS
│   ├── City Market Division
│       ├── City Market PS, VV Puram PS, Upparpet PS
├── South-East Zone
│   ├── Electronic City Division
│   │   ├── Electronic City PS, Bommanahalli PS, Begur PS
│   ├── BTM Layout Division
│       ├── BTM PS, Madiwala PS, Hulimavu PS
```

### Police Station Code Format

```
PS Code: KA-{DISTRICT_CODE}-{SERIAL_3DIGIT}
Example: KA-BLR-C-042 (Whitefield PS, Bangalore City)
         KA-MYS-015 (Devaraja PS, Mysore)
         KA-BGM-023 (Belgaum City PS)

Total PS in Karnataka: ~1100+
Bangalore City: ~110 PS
```

---

## 6. CCTNS Schema Alignment

### FIR Number Format

```
Format: {StateCode}/{DistrictCode}/{PSCode}/{Year}/{SerialNumber}
Example: KA/BLR-C/042/2024/001234

Components:
- StateCode: KA (Karnataka)
- DistrictCode: BLR-C (Bangalore City)
- PSCode: 042 (Whitefield PS)
- Year: 2024
- SerialNumber: 001234 (auto-increment per PS per year)
```

### Section Mapping (IPC → BNS Transition)

```json
{
  "sectionMapping": {
    "IPC_302": { "bns": "BNS_101", "description": "Murder", "category": "Against Body" },
    "IPC_376": { "bns": "BNS_63", "description": "Rape", "category": "Sexual Offence" },
    "IPC_379": { "bns": "BNS_303", "description": "Theft", "category": "Against Property" },
    "IPC_420": { "bns": "BNS_318", "description": "Cheating", "category": "Against Property" },
    "IPC_354": { "bns": "BNS_74", "description": "Outraging Modesty", "category": "Sexual Offence" },
    "IPC_498A": { "bns": "BNS_84", "description": "Cruelty by Husband", "category": "Against Women" },
    "IPC_304A": { "bns": "BNS_106", "description": "Death by Negligence", "category": "Against Body" },
    "IPC_323": { "bns": "BNS_115", "description": "Voluntarily Causing Hurt", "category": "Against Body" },
    "IPC_363": { "bns": "BNS_137", "description": "Kidnapping", "category": "Against Body" },
    "IPC_392": { "bns": "BNS_309", "description": "Robbery", "category": "Against Property" },
    "IPC_406": { "bns": "BNS_316", "description": "Criminal Breach of Trust", "category": "Against Property" },
    "IPC_411": { "bns": "BNS_317", "description": "Receiving Stolen Property", "category": "Against Property" },
    "IPC_120B": { "bns": "BNS_61", "description": "Criminal Conspiracy", "category": "Conspiracy" },
    "IPC_506": { "bns": "BNS_351", "description": "Criminal Intimidation", "category": "Against Body" },
    "IPC_307": { "bns": "BNS_109", "description": "Attempt to Murder", "category": "Against Body" }
  }
}
```

### FIR Status Codes

| Status Code | Status Name | Description |
|------------|-------------|-------------|
| `REG` | Registered | FIR registered, investigation not started |
| `UI` | Under Investigation | IO assigned, active investigation |
| `PT` | Pending Technical | Awaiting forensic/CDR/bank reports |
| `CS_FILED` | Chargesheet Filed | Chargesheet submitted to court |
| `CS_PENDING` | Chargesheet Pending | Within deadline, being prepared |
| `FR` | Final Report (False) | Case found false, closed |
| `FR_M` | Final Report (Mistake of Fact) | Closed as mistake of fact |
| `FR_C` | Final Report (Civil Nature) | Referred to civil court |
| `RCC` | Referred CC | Referred as non-cognizable (private complaint) |
| `TRANSFERRED` | Transferred | Transferred to another PS/state |
| `UNDETECTED` | Undetected | No accused identified, case cold |
| `CONVICTION` | Conviction | Court convicted accused |
| `ACQUITTAL` | Acquittal | Court acquitted accused |
| `COMPOUNDED` | Compounded | Case settled between parties |
| `ABATED` | Abated | Accused died during trial |

### Person Role Codes

| Code | Role | Context |
|------|------|---------|
| `ACC` | Accused | Person charged in FIR |
| `VIC` | Victim | Complainant / injured party |
| `WIT` | Witness | Eye/ear/expert witness |
| `IO` | Investigating Officer | Assigned investigator |
| `SHO` | Station House Officer | PS head |
| `COM` | Complainant | Person filing FIR (may differ from victim) |
| `INF` | Informant | Source of information |
| `MED` | Mediator | Court-appointed mediator |

### Evidence Classification

| Type Code | Type | Sub-types |
|-----------|------|-----------|
| `PHY` | Physical | Fingerprint, DNA, fiber, blood, weapon, tool |
| `DIG` | Digital | CDR, IP logs, chat records, email, social media |
| `DOC` | Documentary | Bank statement, property deed, agreement, letter |
| `ELC` | Electronic | CCTV footage, dashcam, body cam, audio recording |
| `FOR` | Forensic | FSL report, ballistic, chemical, handwriting |
| `TES` | Testimonial | 161 statement, 164 statement, dying declaration |

---

## 7. Data Model — Graph Schema

### Neo4j/Graph Representation

```cypher
// Node Labels
(:FIR {firNumber, dateRegistered, status, summary, sections, psCode})
(:Person {name, age, gender, phone, address, aadharHash})
(:Vehicle {regNumber, chassis, engine, make, model, color})
(:Phone {number, provider, circle})
(:IMEI {imeiNumber, make, model})
(:UPI {upiId, linkedBank})
(:BankAccount {accountNumber, ifsc, holderName})
(:CCTV {cameraId, location, owner})
(:Evidence {evidenceId, type, description})
(:Location {lat, lng, address, type})
(:PoliceStation {psCode, name, district})
(:District {code, name, sp})
(:CrimeCategory {code, name, ipcSections, bnsSections})
(:Organization {name, type})

// Key Relationship Patterns
(p:Person)-[:ACCUSED_IN {role, arrestDate}]->(f:FIR)
(p:Person)-[:VICTIM_IN {lossAmount}]->(f:FIR)
(v:Vehicle)-[:USED_IN {usageType}]->(f:FIR)
(p1:Person)-[:CO_ACCUSED_WITH {firCount}]->(p2:Person)
(p1:Person)-[:SHARES_PHONE_WITH {number}]->(p2:Person)
(a:BankAccount)-[:FINANCIAL_FLOW {amount, timestamp}]->(b:BankAccount)
(f1:FIR)-[:SAME_MODUS_OPERANDI {score}]->(f2:FIR)
(f:FIR)-[:OCCURRED_AT]->(l:Location)
(f:FIR)-[:REGISTERED_AT]->(ps:PoliceStation)
(ps:PoliceStation)-[:BELONGS_TO]->(d:District)
(p:Person)-[:CAPTURED_BY {timestamp}]->(c:CCTV)
```

### Indexes & Constraints

```cypher
// Unique constraints
CREATE CONSTRAINT ON (f:FIR) ASSERT f.firNumber IS UNIQUE;
CREATE CONSTRAINT ON (p:Person) ASSERT p.aadharHash IS UNIQUE;
CREATE CONSTRAINT ON (v:Vehicle) ASSERT v.regNumber IS UNIQUE;
CREATE CONSTRAINT ON (ph:Phone) ASSERT ph.number IS UNIQUE;
CREATE CONSTRAINT ON (i:IMEI) ASSERT i.imeiNumber IS UNIQUE;
CREATE CONSTRAINT ON (ps:PoliceStation) ASSERT ps.psCode IS UNIQUE;

// Performance indexes
CREATE INDEX ON :FIR(status);
CREATE INDEX ON :FIR(dateRegistered);
CREATE INDEX ON :FIR(psCode);
CREATE INDEX ON :Person(name);
CREATE INDEX ON :Person(phone);
CREATE INDEX ON :Location(lat, lng);
CREATE INDEX ON :Evidence(type);
```

### Query Patterns (Common)

```cypher
// Find all connections of a person (2-hop)
MATCH path = (p:Person {name: $name})-[*1..2]-(connected)
RETURN path

// Find co-accused network
MATCH (p:Person)-[:ACCUSED_IN]->(f:FIR)<-[:ACCUSED_IN]-(coAccused:Person)
WHERE p.name = $name
RETURN coAccused, f, count(f) as sharedCases
ORDER BY sharedCases DESC

// Detect shared phone patterns
MATCH (p1:Person)-[:ACCUSED_IN]->(f1:FIR),
      (p2:Person)-[:ACCUSED_IN]->(f2:FIR),
      (p1)-[:SHARES_PHONE_WITH]->(p2)
WHERE f1 <> f2
RETURN p1, p2, collect(distinct f1) + collect(distinct f2) as linkedCases

// Financial flow tracing (multi-hop)
MATCH path = (source:BankAccount)-[:FINANCIAL_FLOW*1..5]->(dest:BankAccount)
WHERE source.accountNumber = $sourceAccount
RETURN path, reduce(total = 0, r in relationships(path) | total + r.amount) as totalFlow

// Hotspot detection
MATCH (f:FIR)-[:OCCURRED_AT]->(l:Location),
      (f)-[:CATEGORIZED_AS]->(c:CrimeCategory {name: $crimeType})
WHERE f.dateRegistered > date() - duration({days: 90})
WITH l, count(f) as incidents
WHERE incidents >= 3
RETURN l, incidents ORDER BY incidents DESC
```

---

## 8. Scalability Considerations

### Data Volume Estimates (Karnataka)

| Entity | Estimated Count | Growth Rate |
|--------|----------------|-------------|
| FIRs | ~500,000/year | 5-8% annually |
| Persons (unique) | ~2,000,000 | Cumulative |
| Vehicles | ~800,000 | Cumulative |
| Phone numbers | ~1,500,000 | Cumulative |
| Relationships | ~10,000,000 | 10x entity growth |
| CCTV records | ~50,000,000/year | High volume |

### Performance Requirements

| Operation | Target Latency | Notes |
|-----------|---------------|-------|
| Single entity lookup | < 100ms | By ID or unique key |
| 2-hop connection query | < 2s | Up to 1000 results |
| Network detection | < 10s | Deep traversal with filters |
| Hotspot calculation | < 5s | Spatial aggregation |
| Full-text search | < 500ms | Across FIR summaries |
| Financial flow trace | < 5s | Up to 5 hops |

# CHECKPOINT 6: Vector Database Test Queries Report

**Date**: 2026-07-22  
**Database**: ChromaDB Persistent Instance (`data/chroma_db`)  
**Total Ingested Chunks**: 593  
**Embedding Model**: `BAAI/bge-small-en-v1.5`  
**Distance Metric**: Cosine Distance  

## Summary of Manual Test Queries

This document records the top-5 retrieved legal chunks for 10 manual test queries covering the **Pakistan Penal Code (PPC)**, **Code of Criminal Procedure (CrPC)**, and the **Constitution of Pakistan**.

---

### Query 1 [Constitution]: "What are the fundamental rights of a citizen regarding arrest and detention?"

| Rank | Act Name | Section / Article | Chunk ID | Cosine Distance | Content Snippet |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | Constitution of Pakistan | 10 | `constitution_article_10_chunk_0` | 0.2778 | 10 Safeguards as to arrest and detention (1) No person who is arrested shall be detained in custody without being informed, as soon as may be, of the grounds for such arrest, nor shall he be denied the right to consult and be defended by a legal practitioner of his choice. (2) Every person who is ar... |
| 2 | Constitution of Pakistan | 19A | `constitution_article_19a_chunk_0` | 0.3091 | 19A.	Right to information: Every citizen shall have the right to have access to information in all matters of public importance subject to regulation and reasonable restrictions imposed by law.... |
| 3 | Constitution of Pakistan | 15 | `constitution_article_15_chunk_0` | 0.3152 | 15	Freedom of movement, etc. Every citizen shall have the right to remain in, and, subject to any reasonable restriction imposed by law in the public interest, enter and move freely throughout Pakistan and to reside and settle in any part thereof.... |
| 4 | Constitution of Pakistan | 9 | `constitution_article_9_chunk_0` | 0.3195 | 9	Security of person. No person shall be deprived of life or liberty save in accordance with law.... |
| 5 | Constitution of Pakistan | 19 | `constitution_article_19_chunk_0` | 0.3278 | 19	Freedom of speech, etc. Every citizen shall have the right to freedom of speech and expression, and there shall be freedom of the press, subject to any reasonable restrictions imposed by law in the interest of the glory of Islam or the integrity, security or defence of Pakistan or any part thereo... |

---

### Query 2 [Constitution]: "What does the Constitution of Pakistan say about freedom of speech and expression?"

| Rank | Act Name | Section / Article | Chunk ID | Cosine Distance | Content Snippet |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | Constitution of Pakistan | 19 | `constitution_article_19_chunk_0` | 0.1568 | 19	Freedom of speech, etc. Every citizen shall have the right to freedom of speech and expression, and there shall be freedom of the press, subject to any reasonable restrictions imposed by law in the interest of the glory of Islam or the integrity, security or defence of Pakistan or any part thereo... |
| 2 | Constitution of Pakistan | 17 | `constitution_article_17_chunk_0` | 0.2591 | 17.	Freedom of association: (1)	Every citizen shall have the right to form associations or unions, subject to any reasonable restrictions imposed by law in the interest of sovereignty or integrity of Pakistan, public order or morality. (2)	Every citizen, not being in the service of Pakistan, shall h... |
| 3 | Constitution of Pakistan | 15 | `constitution_article_15_chunk_0` | 0.2914 | 15	Freedom of movement, etc. Every citizen shall have the right to remain in, and, subject to any reasonable restriction imposed by law in the public interest, enter and move freely throughout Pakistan and to reside and settle in any part thereof.... |
| 4 | Constitution of Pakistan | 23 | `constitution_article_23_chunk_0` | 0.3042 | 23	Provision as to property. Every citizen shall have the right to acquire, hold and dispose of property in any part of Pakistan, subject to the Constitution and any reasonable restrictions imposed by law in the public interest.... |
| 5 | Constitution of Pakistan | 27 | `constitution_article_27_chunk_0` | 0.3381 | 27.	Safeguard against discrimination in services. (1)	No citizen otherwise qualified for appointment in the service of Pakistan shall be discriminated against in respect of any such appointment on the ground only of race, religion, caste, sex, residence or place of birth: Provided that, for a period... |

---

### Query 3 [Constitution]: "Is free and compulsory education guaranteed to all children in Pakistan?"

| Rank | Act Name | Section / Article | Chunk ID | Cosine Distance | Content Snippet |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | Constitution of Pakistan | 25A | `constitution_article_25a_chunk_0` | 0.2314 | 25A.	Right to education: The State shall provide free and compulsory education to all children of the age of five to sixteen years in such manner as may be determined by law.... |
| 2 | Constitution of Pakistan | 11 | `constitution_article_11_chunk_0` | 0.3163 | 11	Slavery, forced labour, etc. prohibited (1)	Slavery is non-existent and forbidden and no law shall permit or facilitate its introduction into Pakistan in any form. (2)	All forms of forced labour and traffic in human beings are prohibited. (3)	No child below the age of fourteen years shall be enga... |
| 3 | Constitution of Pakistan | 15 | `constitution_article_15_chunk_0` | 0.3282 | 15	Freedom of movement, etc. Every citizen shall have the right to remain in, and, subject to any reasonable restriction imposed by law in the public interest, enter and move freely throughout Pakistan and to reside and settle in any part thereof.... |
| 4 | Constitution of Pakistan | 23 | `constitution_article_23_chunk_0` | 0.3447 | 23	Provision as to property. Every citizen shall have the right to acquire, hold and dispose of property in any part of Pakistan, subject to the Constitution and any reasonable restrictions imposed by law in the public interest.... |
| 5 | Constitution of Pakistan | 22 | `constitution_article_22_chunk_0` | 0.3472 | 22	Safeguards as to educational institutions in respect of religion, etc. (1)	No person attending any educational institution shall be required to receive religious instruction, or take part in any religious ceremony, or attend religious worship, if such instruction, ceremony or worship relates to a... |

---

### Query 4 [PPC]: "What is the legal definition and punishment for theft under the Pakistan Penal Code?"

| Rank | Act Name | Section / Article | Chunk ID | Cosine Distance | Content Snippet |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | Constitution of Pakistan | 12 | `constitution_article_12_chunk_0` | 0.3142 | 12	Protection against retrospective punishment (1)	No law shall authorize the punishment of a person:- (a)	for an act or omission that was not punishable by law at the time of the act or omission; or (b)	for an offence by a penalty greater than, or of a kind different from, the penalty prescribed by... |
| 2 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_6` | 0.3160 | ACT: Code of Criminal Procedure, 1898 SECTION: 93C TITLE: Service and execution in Pakistan of processes received from outside Pakistan CHAPTER:  ============================================================  93C. Service and execution in Pakistan of processes received from outside Pakistan.  CHAPTER... |
| 3 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_30` | 0.3527 | ACT: Code of Criminal Procedure, 1898 SECTION: 562 TITLE: Powers of Court to release certain convicted offenders on probation of good CHAPTER:  ============================================================  562. Powers of Court to release certain convicted offenders on probation of good  conduct inst... |
| 4 | Constitution of Pakistan | 13 | `constitution_article_13_chunk_0` | 0.3561 | 13	Protection against double punishment and self incrimination. No person:- (a)	shall be prosecuted or punished for the same offence more than once; or (b)	shall, when accused of an offence, be compelled to be a witness against himself.... |
| 5 | Constitution of Pakistan | 10 | `constitution_article_10_chunk_0` | 0.3569 | 10 Safeguards as to arrest and detention (1) No person who is arrested shall be detained in custody without being informed, as soon as may be, of the grounds for such arrest, nor shall he be denied the right to consult and be defended by a legal practitioner of his choice. (2) Every person who is ar... |

---

### Query 5 [PPC]: "What constitutes murder and culpable homicide under PPC?"

| Rank | Act Name | Section / Article | Chunk ID | Cosine Distance | Content Snippet |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_20` | 0.3621 | ACT: Code of Criminal Procedure, 1898 SECTION: 382C TITLE: Scandalous or false and frivolous pleas to be considered in passing sentence CHAPTER:  ============================================================  382C. Scandalous or false and frivolous pleas to be considered in passing sentence.   ACT: C... |
| 2 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_13` | 0.3727 | ACT: Code of Criminal Procedure, 1898 SECTION: 196 TITLE: Prosecution for offences against the state CHAPTER:  ============================================================  196. Prosecution for offences against the state.   ACT: Code of Criminal Procedure, 1898 SECTION: 196A TITLE: Prosecution for c... |
| 3 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_30` | 0.3746 | ACT: Code of Criminal Procedure, 1898 SECTION: 562 TITLE: Powers of Court to release certain convicted offenders on probation of good CHAPTER:  ============================================================  562. Powers of Court to release certain convicted offenders on probation of good  conduct inst... |
| 4 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_19` | 0.3789 | ACT: Code of Criminal Procedure, 1898 SECTION: 371 TITLE: Copy of judgment, etc, to be given to accused CHAPTER:  ============================================================  371. Copy of judgment, etc, to be given to accused.  Case of person sentenced to death.   ACT: Code of Criminal Procedure, 1... |
| 5 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_21` | 0.3791 | ACT: Code of Criminal Procedure, 1898 SECTION: 400 TITLE: Return of warrant on execution of sentence CHAPTER:  ============================================================  400. Return of warrant on execution of sentence.  CHAPTER XXIX  OF SUSPENSIONS, REMISSIONS AND COMMUNICATIONS OF  SENTENCES.... |

---

### Query 6 [PPC]: "What are the legal provisions regarding criminal breach of trust?"

| Rank | Act Name | Section / Article | Chunk ID | Cosine Distance | Content Snippet |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | Constitution of Pakistan | 10 | `constitution_article_10_chunk_1` | 0.3632 | which the order has been made, and shall afford him the earliest opportunity of making a representation against the order: Provided that the authority making any such order may refuse to disclose facts which such authority considers it to be against the public interest to disclose. (6) The authority... |
| 2 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_27` | 0.3660 | ACT: Code of Criminal Procedure, 1898 SECTION: 519 TITLE: Payment to innocent purchaser of money found on accused CHAPTER:  ============================================================  519. Payment to innocent purchaser of money found on accused.   ACT: Code of Criminal Procedure, 1898 SECTION: 520... |
| 3 | Constitution of Pakistan | 24 | `constitution_article_24_chunk_0` | 0.3737 | 24	Protection of property rights. (1)	No person shall be compulsorily deprived of his property save in accordance with law. (2)	No property shall be compulsorily acquired or taken possession of save for a public purpose, and save by the authority of law which provides for compensation therefore and... |
| 4 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_13` | 0.3850 | ACT: Code of Criminal Procedure, 1898 SECTION: 196 TITLE: Prosecution for offences against the state CHAPTER:  ============================================================  196. Prosecution for offences against the state.   ACT: Code of Criminal Procedure, 1898 SECTION: 196A TITLE: Prosecution for c... |
| 5 | Constitution of Pakistan | 13 | `constitution_article_13_chunk_0` | 0.3857 | 13	Protection against double punishment and self incrimination. No person:- (a)	shall be prosecuted or punished for the same offence more than once; or (b)	shall, when accused of an offence, be compelled to be a witness against himself.... |

---

### Query 7 [PPC]: "What is cheating and dishonestly inducing delivery of property under PPC?"

| Rank | Act Name | Section / Article | Chunk ID | Cosine Distance | Content Snippet |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | Constitution of Pakistan | 24 | `constitution_article_24_chunk_0` | 0.3652 | 24	Protection of property rights. (1)	No person shall be compulsorily deprived of his property save in accordance with law. (2)	No property shall be compulsorily acquired or taken possession of save for a public purpose, and save by the authority of law which provides for compensation therefore and... |
| 2 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_29` | 0.3933 | ACT: Code of Criminal Procedure, 1898 SECTION: 546A TITLE: Order of payment of certain fees paid by complainant in non­cognizable cases CHAPTER:  ============================================================  546A. Order of payment of certain fees paid by complainant in non­cognizable cases.   ACT: C... |
| 3 | Constitution of Pakistan | 23 | `constitution_article_23_chunk_0` | 0.3960 | 23	Provision as to property. Every citizen shall have the right to acquire, hold and dispose of property in any part of Pakistan, subject to the Constitution and any reasonable restrictions imposed by law in the public interest.... |
| 4 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_27` | 0.3986 | ACT: Code of Criminal Procedure, 1898 SECTION: 519 TITLE: Payment to innocent purchaser of money found on accused CHAPTER:  ============================================================  519. Payment to innocent purchaser of money found on accused.   ACT: Code of Criminal Procedure, 1898 SECTION: 520... |
| 5 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_6` | 0.4018 | ACT: Code of Criminal Procedure, 1898 SECTION: 93C TITLE: Service and execution in Pakistan of processes received from outside Pakistan CHAPTER:  ============================================================  93C. Service and execution in Pakistan of processes received from outside Pakistan.  CHAPTER... |

---

### Query 8 [CrPC]: "What is the procedure for recording an FIR under section 154 of CrPC?"

| Rank | Act Name | Section / Article | Chunk ID | Cosine Distance | Content Snippet |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_18` | 0.3640 | ACT: Code of Criminal Procedure, 1898 SECTION: 351 TITLE: Detention of offenders attending Court CHAPTER:  ============================================================  351. Detention of offenders attending Court.   ACT: Code of Criminal Procedure, 1898 SECTION: 352 TITLE: Courts to be open CHAPTER:... |
| 2 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_23` | 0.3649 | ACT: Code of Criminal Procedure, 1898 SECTION: 431 TITLE: Abatement of appeals CHAPTER:  ============================================================  431. Abatement of appeals.  CHAPTER XXXII  OF REFERENCE AND REVISION 432­434. [Omitted.]   ACT: Code of Criminal Procedure, 1898 SECTION: 435 TITLE:... |
| 3 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_30` | 0.3782 | ACT: Code of Criminal Procedure, 1898 SECTION: 562 TITLE: Powers of Court to release certain convicted offenders on probation of good CHAPTER:  ============================================================  562. Powers of Court to release certain convicted offenders on probation of good  conduct inst... |
| 4 | Constitution of Pakistan | 10 | `constitution_article_10_chunk_1` | 0.3846 | which the order has been made, and shall afford him the earliest opportunity of making a representation against the order: Provided that the authority making any such order may refuse to disclose facts which such authority considers it to be against the public interest to disclose. (6) The authority... |
| 5 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_11` | 0.3846 | ACT: Code of Criminal Procedure, 1898 SECTION: 164A TITLE: Medical examination of victim of rape, etc CHAPTER:  ============================================================  164A. Medical examination of victim of rape, etc.   ACT: Code of Criminal Procedure, 1898 SECTION: 164B TITLE: DNA test CHAPTE... |

---

### Query 9 [CrPC]: "When can a police officer arrest an accused person without a warrant?"

| Rank | Act Name | Section / Article | Chunk ID | Cosine Distance | Content Snippet |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | Constitution of Pakistan | 10 | `constitution_article_10_chunk_0` | 0.3081 | 10 Safeguards as to arrest and detention (1) No person who is arrested shall be detained in custody without being informed, as soon as may be, of the grounds for such arrest, nor shall he be denied the right to consult and be defended by a legal practitioner of his choice. (2) Every person who is ar... |
| 2 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_3` | 0.3550 | ACT: Code of Criminal Procedure, 1898 SECTION: 53 TITLE: Power to seize offensive weapons CHAPTER:  ============================================================  53. Power to seize offensive weapons.   ACT: Code of Criminal Procedure, 1898 SECTION: 53A TITLE: Examination of person accused of rape, e... |
| 3 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_5` | 0.3587 | ACT: Code of Criminal Procedure, 1898 SECTION: 81 TITLE: Person arrested to be brought before Court without delay CHAPTER:  ============================================================  81. Person arrested to be brought before Court without delay.   ACT: Code of Criminal Procedure, 1898 SECTION: 82... |
| 4 | Constitution of Pakistan | 10 | `constitution_article_10_chunk_1` | 0.3618 | which the order has been made, and shall afford him the earliest opportunity of making a representation against the order: Provided that the authority making any such order may refuse to disclose facts which such authority considers it to be against the public interest to disclose. (6) The authority... |
| 5 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_4` | 0.3843 | ACT: Code of Criminal Procedure, 1898 SECTION: 70 TITLE: Service when person summoned cannot be found CHAPTER:  ============================================================  70. Service when person summoned cannot be found.   ACT: Code of Criminal Procedure, 1898 SECTION: 71 TITLE: Procedure when se... |

---

### Query 10 [CrPC]: "What are the legal rules and conditions for granting bail in criminal cases?"

| Rank | Act Name | Section / Article | Chunk ID | Cosine Distance | Content Snippet |
| :---: | :--- | :---: | :--- | :---: | :--- |
| 1 | Constitution of Pakistan | 10 | `constitution_article_10_chunk_0` | 0.3484 | 10 Safeguards as to arrest and detention (1) No person who is arrested shall be detained in custody without being informed, as soon as may be, of the grounds for such arrest, nor shall he be denied the right to consult and be defended by a legal practitioner of his choice. (2) Every person who is ar... |
| 2 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_29` | 0.3540 | ACT: Code of Criminal Procedure, 1898 SECTION: 546A TITLE: Order of payment of certain fees paid by complainant in non­cognizable cases CHAPTER:  ============================================================  546A. Order of payment of certain fees paid by complainant in non­cognizable cases.   ACT: C... |
| 3 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_27` | 0.3564 | ACT: Code of Criminal Procedure, 1898 SECTION: 519 TITLE: Payment to innocent purchaser of money found on accused CHAPTER:  ============================================================  519. Payment to innocent purchaser of money found on accused.   ACT: Code of Criminal Procedure, 1898 SECTION: 520... |
| 4 | Constitution of Pakistan | 10 | `constitution_article_10_chunk_1` | 0.3566 | which the order has been made, and shall afford him the earliest opportunity of making a representation against the order: Provided that the authority making any such order may refuse to disclose facts which such authority considers it to be against the public interest to disclose. (6) The authority... |
| 5 | Code of Criminal Procedure, 1898 | Unknown | `crpc_chunk_15` | 0.3587 | ACT: Code of Criminal Procedure, 1898 SECTION: 241 TITLE: Procedure in trial of cases CHAPTER:  ============================================================  241. Procedure in trial of cases.   ACT: Code of Criminal Procedure, 1898 SECTION: 241A TITLE: Supply of statements and documents to the accus... |

---

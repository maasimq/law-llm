import os
import re
import csv

raw_text = """8	Laws inconsistent with or in derogation of fundamental rights to be void.
(1)	Any law, or any custom or usage having the force of law, in so far as it is inconsistent with the rights conferred by this Chapter, shall, to the extent of such inconsistency, be void.
 
(2)	The State shall not make any law which takes away or abridges the rights so conferred and any law made in contravention of this clause shall, to the extent of such contravention, be void.
 
(3)	The provisions of this Article shall not apply to :-
(a)	any law relating to members of the Armed Forces, or of the police or of such other forces as are charged with the maintenance of public order, for the purpose of ensuring the proper discharge of their duties or the maintenance of discipline among them; or
 17[
(b)	any of the:-
(i)	laws specified in the First Schedule as in force immediately before the commencing day or as amended by any of the laws specified in that Schedule;
(ii)	other laws specified in Part I of the First Schedule;
] 17 and no such law nor any provision thereof shall be void on the ground that such law or provision is inconsistent with, or repugnant to, any provision of this Chapter.
 
(4)	Notwithstanding anything contained in paragraph (b) of clause (3), within a period of two years from the commencing day, the appropriate Legislature shall bring the laws specified in  19[Part II of the First Schedule] 19 into conformity with the rights conferred by this Chapter:
Provided that the appropriate Legislature may by resolution extend the said period of two years by a period not exceeding six months.
Explanation:- If in respect of any law  20[Majlis-e-Shoora (Parliament)] 20 is the appropriate Legislature, such resolution shall be a resolution of the National Assembly.
 
(5)	The rights conferred by this Chapter shall not be suspended except as expressly provided by the Constitution.
 
 
9	Security of person.
No person shall be deprived of life or liberty save in accordance with law.
 
 21[
9A	Clean and healthy environment
Every person shall be entitled to a clean, healthy and sustainable environment.
 
] 21
10	Safeguards as to arrest and detention
(1)	No person who is arrested shall be detained in custody without being informed, as soon as may be, of the grounds for such arrest, nor shall he be denied the right to consult and be defended by a legal practitioner of his choice.
 
(2)	Every person who is arrested and detained in custody shall be produced before a magistrate within a period of twenty-four hours of such arrest, excluding the time necessary for the journey from the place of arrest to the court of the nearest magistrate, and no such person shall be detained in :custody beyond the said period without the authority of a magistrate.
 
(3)	Nothing in clauses (1) and (2) shall apply to any person who is arrested or detained under any law providing for preventive detention.
 
(4)	No law providing for preventive detention shall be made except to deal with persons acting in a manner prejudicial to the integrity, security or defence of Pakistan or any part thereof, or external affairs of Pakistan, or public order, or the maintenance of supplies or services, and no such law shall authorise the detention of a person for a period exceeding  22[three months] 22 unless the appropriate Review Board has, after affording him an opportunity of being heard in person, reviewed his case and reported, before the expiration of the said period, that there is, in its opinion, sufficient cause for such detention, and, if the detention is continued after the said period of  23[three months] 23, unless the appropriate Review Board has reviewed his case and reported, before the expiration of each period of three months, that there is, in its opinion, sufficient cause for such detention.
Explanation-I: In this Article, "the appropriate Review Board" means:-
(i)	in the case of a person detained under a Federal law, a Board appointed by the Chief Justice of  24[Supreme Court of] 24 Pakistan and consisting of a Chairman and two other persons, each of whom is or has been a Judge of the Supreme Court or a High Court; and
(ii)	in the case of a Person detained under a Provincial law, a Board appointed by the Chief Justice of the High Court concerned and consisting of a Chairman and two other persons, each of whom is or has been a Judge of a High Court.
Explanation-II: The opinion of a Review Board shall be expressed in terms of the views of the majority of its members.
 
(5)	When any person is detained in pursuance of an order made under any law providing for preventive detention, the authority making the order shall,  25[within fifteen days] 25 from such detention, communicate to such person the grounds on which the order has been made, and shall afford him the earliest opportunity of making a representation against the order:
Provided that the authority making any such order may refuse to disclose facts which such authority considers it to be against the public interest to disclose.
 
(6)	The authority making the order shall furnish to the appropriate Review Board all documents relevant to the case unless a certificate, signed by a Secretary to the Government concerned, to the effect that it is not in the public interest to furnish any documents, is produced.
 
(7)	Within a period of twenty-four months commencing on the day of his first detention in pursuance of an order made under a law providing for preventive detention, no person shall be detained in pursuance of any such order for more than a total period of eight months in the case of a person detained for acting in a manner prejudicial to public order and twelve months in any other case:
Provided that this clause shall not apply to any person who is employed by, or works for, or acts on instructions received from, the enemy  26[or who is acting or attempting to act in a manner prejudicial to the integrity, security or defence of Pakistan or any part thereof or who commits or attempts to commit any act which amounts to an anti-national activity as defined in a Federal law or is a member of any association which has for its objects, or which indulges in, any such anti-national activity] 26.
 
(8)	The appropriate Review Board shall determine the place of detention of the person detained and fix a reasonable subsistence allowance for his family.
 
(9)	Nothing in this Article shall apply to any person who for the time being is an enemy alien.
 
 
 27[
10A.	Right to fair trial:
For the determination of his civil rights and obligations or in any criminal charge against him a person shall be entitled to a fair trial and due process.
 
] 27
11	Slavery, forced labour, etc. prohibited
(1)	Slavery is non-existent and forbidden and no law shall permit or facilitate its introduction into Pakistan in any form.
 
(2)	All forms of forced labour and traffic in human beings are prohibited.
 
(3)	No child below the age of fourteen years shall be engaged in any factory or mine or any other hazardous employment.
 
(4)	Nothing in this Article shall be deemed to affect compulsory service:-
(a)	by any person undergoing punishment for an offence against any law; or
(b)	required by any law for public purpose provided that no compulsory service shall be of a cruel nature or incompatible with human dignity.
 
 
12	Protection against retrospective punishment
(1)	No law shall authorize the punishment of a person:-
(a)	for an act or omission that was not punishable by law at the time of the act or omission; or
(b)	for an offence by a penalty greater than, or of a kind different from, the penalty prescribed by law for that offence at the time the offence was committed.
 
(2)	Nothing in clause (1) or in Article 270 shall apply to any law making acts of abrogation or subversion of a Constitution in force in Pakistan at any time since the twenty-third day of March, one thousand nine hundred and fifty-six, an offence.
 
 
13	Protection against double punishment and self incrimination.
No person:-
(a)	shall be prosecuted or punished for the same offence more than once; or
(b)	shall, when accused of an offence, be compelled to be a witness against himself.
 
14	Inviolability of dignity of man, etc.
(1)	The dignity of man and, subject to law, the privacy of home, shall be inviolable.
 
(2)	No person shall be subjected to torture for the purpose of extracting evidence.
 
 
15	Freedom of movement, etc.
Every citizen shall have the right to remain in, and, subject to any reasonable restriction imposed by law in the public interest, enter and move freely throughout Pakistan and to reside and settle in any part thereof.
 
16	Freedom of assembly.
Every citizen shall have the right to assemble peacefully and without arms, subject to any reasonable restrictions imposed by law in the interest of public order.
 
 28[
17.	Freedom of association:
(1)	Every citizen shall have the right to form associations or unions, subject to any reasonable restrictions imposed by law in the interest of sovereignty or integrity of Pakistan, public order or morality.
 
(2)	Every citizen, not being in the service of Pakistan, shall have the right to form or be a member of a political party, subject to any reasonable restrictions imposed by law in the interest of the sovereignty or integrity of Pakistan and such law shall provide that where the Federal Government declares that any political party has been formed or is operating in a manner prejudicial to the soverignty or integrity of Pakistan, the Federal Government shall, within fifeen days of such declaration, refer the matter to the  36[Federal Constitutional Court of Pakistan] 36 whose decision on such reference shall be final.
 
(3)	Every political party shall account for the source of its funds in accordance with law.
 
 
] 28
18	Freedom of trade, business or profession.
Subject to such qualifications, if any, as may be prescribed by law, every citizen shall have the right to enter upon any lawful profession or occupation, and to conduct any lawful trade or business:
Provided that nothing in this Article shall prevent:-
(a)	the regulation of any trade or profession by a licensing system; or
(b)	the regulation of trade, commerce or industry in the interest of free competition therein; or
(c)	the carrying on, by the Federal Government or a Provincial Government, or by a corporation controlled by any such Government, of any trade, business, industry or service, to the exclusion, complete or partial, of other persons.
 
19	Freedom of speech, etc.
Every citizen shall have the right to freedom of speech and expression, and there shall be freedom of the press, subject to any reasonable restrictions imposed by law in the interest of the glory of Islam or the integrity, security or defence of Pakistan or any part thereof, friendly relations with foreign States, public order, decency or morality, or in relation to contempt of court,  37[commission of] 37 or incitement to an offence.
 
 38[
19A.	Right to information:
Every citizen shall have the right to have access to information in all matters of public importance subject to regulation and reasonable restrictions imposed by law.
 
] 38
20	Freedom to profess religion and to manage religious institutions.
Subject to law, public order and morality:-
(a)	every citizen shall have the right to profess, practice and propagate his religion; and
(b)	every religious denomination and every sect thereof shall have the right to establish, maintain and manage its religious institutions.
 
21	Safeguard against taxation for purposes of any particular religion.
No person shall be compelled to pay any special tax the proceeds of which are to be spent on the propagation or maintenance of any religion other than his own.
 
22	Safeguards as to educational institutions in respect of religion, etc.
(1)	No person attending any educational institution shall be required to receive religious instruction, or take part in any religious ceremony, or attend religious worship, if such instruction, ceremony or worship relates to a religion other than his own.
 
(2)	In respect of any religious institution, there shall be no discrimination against any community in the granting of exemption or concession in relation to taxation.
 
(3)	Subject to law:
(a)	no religious community or denomination shall be prevented from providing religious instruction for pupils of that community or denomination in any educational institution maintained wholly by that community or denomination; and
(b)	no citizen shall be denied admission to any educational institution receiving aid from public revenues on the ground only of race, religion, caste or place of birth.
 
(4)	Nothing in this Article shall prevent any public authority from making provision for the advancement of any socially or educationally backward class of citizens.
 
 
23	Provision as to property.
Every citizen shall have the right to acquire, hold and dispose of property in any part of Pakistan, subject to the Constitution and any reasonable restrictions imposed by law in the public interest.
 
24	Protection of property rights.
(1)	No person shall be compulsorily deprived of his property save in accordance with law.
 
(2)	No property shall be compulsorily acquired or taken possession of save for a public purpose, and save by the authority of law which provides for compensation therefore and either fixes the amount of compensation or specifies the principles on and the manner in which compensation is to be determined and given.
 
(3)	Nothing in this Article shall affect the validity of :-
(a)	any law permitting the compulsory acquisition or taking possession of any property for preventing danger to life, property or public health; or
(b)	any law permitting the taking over of any property which has been acquired by, or come into the possession of, any person by any unfair means, or in any manner, contrary to law; or
(c)	any law relating to the acquisition, administration or disposal of any property which is or is deemed to be enemy property or evacuee property under any law (not being property which has ceased to be evacuee property under any law); or
(d)	any law providing for the taking over of the management of any property by the State for a limited period, either in the public interest or in order to secure the proper management of the property, or for the benefit of its owner; or
(e)	any law providing for the acquisition of any class of property for the purpose of
(i)	providing education and medical aid to all or any specified class of citizens or
(ii)	providing housing and public facilities and services such as roads, water supply, sewerage, gas and electric power to all or any specified class of citizens; or
(iii)	providing maintenance to those who, on account of unemployment, sickness, infirmity or old age, are unable to maintain themselves ; or
(f)	any existing law or any law made in pursuance of Article 253.
 
(4)	The adequacy or otherwise of any compensation provided for by any such law as is referred to in this Article, or determined in pursuance thereof, shall not be called in question in any court.
 
 
25	Equality of citizens.
(1)	All citizens are equal before law and are entitled to equal protection of law.
 
(2)	There shall be no discrimination on the basis of sex  39[] 39.
 
(3)	Nothing in this Article shall prevent the State from making any special provision for the protection of women and children.
 
 
 40[
25A.	Right to education:
The State shall provide free and compulsory education to all children of the age of five to sixteen years in such manner as may be determined by law.
 
] 40
26.	Non-discrimination in respect of access to public places.
(1)	In respect of access to places of public entertainment or resort not intended for religious purposes only, there shall be no discrimination against any citizen on the ground only of race, religion, caste, sex, residence or place of birth.
 
(2)	Nothing in clause (1) shall prevent the State from making any special provision for women and children.
 
 
27.	Safeguard against discrimination in services.
(1)	No citizen otherwise qualified for appointment in the service of Pakistan shall be discriminated against in respect of any such appointment on the ground only of race, religion, caste, sex, residence or place of birth:
Provided that, for a period not exceeding  41[forty] 41 years from the commencing day, posts may be reserved for persons belonging to any class or area to secure their adequate representation in the service of Pakistan:
Provided further that, in the interest of the said service, specified posts or services may be reserved for members of either sex if such posts or services entail the performance of duties and functions which cannot be adequately performed by members of the other sex 43[:] 43
 44[Provided also that under-representation of any class or area in the service of Pakistan may be redressed in such manner as may be determined by an Act of Majlis-e-Shoora (Parliament).] 44
 
(2)	Nothing in clause (1) shall prevent any Provincial Government, or any local or other authority in a Province, from prescribing, in relation to any post or class of service under that Government or authority, conditions as to residence in the Province. for a period not exceeding three years, prior to appointment under that Government or authority.
 
 
28	Preservation of language, script and culture.
Subject to Article 251 any section of citizens having a distinct language, script or culture shall have the right to preserve and promote the same and subject to law, establish institutions for that purpose.
"""

def clean_text(text):
    # Split text into lines to process carefully
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # If the line is just a reference number bracket like " 17[" or "] 17", skip it entirely
        if re.match(r'^\s*\d+\[\s*$', line) or re.match(r'^\s*\]\s*\d+\s*$', line):
            continue
        # Strip inline bracket references like " 19[Part II of the First Schedule] 19" -> "Part II of the First Schedule"
        line = re.sub(r'\s*\d+\[(.*?)\]\s*\d+', r' \1', line)
        # Fix stray colons
        line = line.replace(':custody', 'custody')
        # Remove empty brackets like []
        line = line.replace('[]', '')
        # Remove trailing/leading spaces
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    
    # Rejoin with newlines
    return '\n'.join(cleaned_lines)

def process_constitution():
    clean_dir = os.path.join("data", "clean")
    os.makedirs(clean_dir, exist_ok=True)
    
    # Delete old index to rewrite it properly
    csv_file = os.path.join(clean_dir, "data_index.csv")
    if os.path.isfile(csv_file):
        os.remove(csv_file)
        
    cleaned_all = clean_text(raw_text)
    
    # Split by Article. Regex matches start of line, number (and maybe letter), optional dot, then space or tab.
    # Since we stripped spaces above, it will be at the start of a line.
    articles_raw = re.split(r'\n(?=\d+[A-Z]?\.?\s)', cleaned_all)
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'act_name', 'section_article_number', 'word_count'])
            
        for article in articles_raw:
            article = article.strip()
            if not article:
                continue
                
            # Extract article number
            match = re.match(r'^(\d+[A-Z]?)\.?', article)
            if match:
                art_num = match.group(1)
                filename = f"constitution_article_{art_num.lower()}.txt"
                filepath = os.path.join(clean_dir, filename)
                
                word_count = len(article.split())
                
                with open(filepath, 'w', encoding='utf-8') as out_f:
                    out_f.write(article)
                    
                writer.writerow([filename, 'Constitution of Pakistan', art_num, word_count])
                print(f"Saved {filename} with word count {word_count}")
            else:
                print("Could not match article number for snippet:")
                print(article[:50])

if __name__ == "__main__":
    process_constitution()

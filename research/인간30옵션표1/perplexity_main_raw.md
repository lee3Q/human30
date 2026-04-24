---
captured: 2026-04-08 15:17:34
source: clipboard
status: unprocessed
tag: p2
---

# Behavioral Predictors for Agent-Based Adult Behavior Simulation: Literature Overview

## Overview

This report synthesizes meta-analyses and large longitudinal studies relevant to designing a character-generation system for a 30-agent behavioral simulation of adult functioning.
It focuses on observable variables with demonstrated predictive validity for social, interpersonal, and life-course outcomes, prioritizing effect sizes from meta-analytic work and long-term cohort data.[1][2]


## 1. Physical Attributes and Adult Social/Interpersonal Behavior

### 1.1 Facial Attractiveness

Large meta-analyses show that facial/physical attractiveness has small-to-moderate but consistent effects on how adults are evaluated and treated, and on some behavioral outcomes.
Langlois et al. (2000, *Psychological Bulletin*) aggregated 11 meta-analyses and found that attractive adults are judged more positively, treated more positively, and display somewhat more positive behaviors and traits than unattractive adults, with typical effect sizes in the small-to-moderate range (around d ≈ 0.20–0.30 for behavioral/trait measures).[3][1]

In the occupational domain, Hosoda, Stone-Romero, and Coats (2003, *Personnel Psychology*) meta-analyzed experimental studies and reported a weighted mean effect size of d = 0.37 for physical attractiveness on job-related outcomes such as hiring recommendations, performance evaluations, and promotion decisions.[4][5]
Prospective cohort data also show that adolescent attractiveness predicts higher socioeconomic status in adulthood even after adjusting for family background (Benzeval, 2013, *PLoS One*).[6]


### 1.2 Height

Judge and Cable (2004, *Journal of Applied Psychology*) combined meta-analytic and large-sample analyses to study height and workplace success.[2][7]
Their meta-analysis found that height is substantially related to social esteem (ρ ≈ 0.41), and more modestly to leader emergence (ρ ≈ 0.24) and job performance (ρ ≈ 0.18).[2]
Across four large datasets (total N ≈ 8,590), each additional standard deviation of height predicted significantly higher income (β ≈ 0.26) even after controlling for sex, age, and weight, implying a non-trivial “height premium.”[8][2]

These effect sizes make height a moderately strong physical predictor of social status and leadership-related behavior compared with many other individual-difference variables.


### 1.3 Body Morphology: BMI, Obesity, and Weight Stigma

Research distinguishes between health effects of higher body mass index (BMI) and social/behavioral effects mediated by weight stigma.
A meta-analysis of weight stigma (105 studies; N ≈ 59,000) by Emmer, Bosnjak, and Mata (2019, *Obesity Reviews*) found a medium-to-large negative association between experienced weight stigma and mental health (r = −0.35), with stronger effects at higher BMI.[9][10][11]

Qualitative and quantitative reviews show that obesity and higher BMI are associated with discrimination in hiring, promotion, and pay.[12][13]
Giel et al. (2010, *Obesity Facts*) reviewed work-setting studies and concluded that obesity is a general barrier to employment and professional success, with consistent evidence of negative stereotypes and biased treatment of higher-weight individuals.[12]
Mendelian-randomization work suggests that high BMI causally increases risk of sickness/disability status and lowers household income, partly through health and possibly discrimination mechanisms (Morris et al., 2021, *International Journal of Obesity*).[14]

In simulations, BMI and/or weight-stigma exposure can plausibly be modeled as predictors of lower mental health, reduced labor-force attachment (via disability), and lower income, with social-exclusion dynamics moderated by culture.


### 1.4 Chronic Illness and Disability

Chronic illness is strongly associated with social dysfunction, though meta-analytically synthesized effect sizes are less standardized than for attractiveness or BMI.
A hospital-based survey of 300 adults with chronic psychiatric and non-psychiatric illnesses found that 74 percent exhibited mild-to-severe social dysfunction as measured by the Social Dysfunction Rating Scale (Linn), indicating substantial impairment in social interactions, self-perception, and role functioning (Khawaja & Hamid, 2016).[15]

Systematic reviews of digital health interventions in older adults with chronic diseases show that baseline chronic illness is associated with reduced quality of life, and that interventions can meaningfully improve general and disease-specific quality of life and mental health (SMD ≈ 0.36–0.54), highlighting the size of the underlying impairment (Hu et al., 2026, *Frontiers in Aging*).[16]
For simulation purposes, chronic illness status is a strong candidate variable to decrease social participation and increase risk for depression and unemployment, though specific behavioral effect sizes vary by condition.


### 1.5 Genital Morphology, Genital Self-Image, and Body Image

Most research focuses on *genital self-image* (subjective evaluation) rather than objective genital morphology.
Herbenick and colleagues developed the Female Genital Self-Image Scale (FGSIS) and showed in a large U.S. sample (N ≈ 1,937) that higher genital self-image scores are significantly associated with better sexual function across all FSFI subscales (desire, arousal, lubrication, orgasm, satisfaction, pain) and with greater engagement in sexual and genital health behaviors (Herbenick et al., 2010, 2011, *Journal of Sexual Medicine*).[17][18][19][20]

Recent work on male genital self-image likewise finds that a more favorable perception of penis size is moderately associated with better erectile function and higher self-esteem (ρ ≈ 0.33 for perceived larger-than-average size and erectile function; da Silva et al., 2026, *Sexual Medicine*; see also 2024 work linking male genital self-image to sexual function and depression/anxiety).[21][22]
A 2025 review of genital self-image and sexual function concludes that positive genital self-image is consistently associated with better sexual desire, arousal, and satisfaction across genders.[23]

More general body image also predicts sexual functioning and relationship satisfaction.
Studies of women show that body image dissatisfaction predicts greater orgasm difficulties and lower sexual relationship satisfaction (Horvath et al., 2020, *Sexual Medicine*; Pujols et al., 2010; Meltzer & McNulty, 2010, *Journal of Family Psychology*).[24][25][26]
Thus, subjective genital/body image appears to be a meaningful predictor of sexual behavior patterns, couple functioning, and mental health, with effect sizes typically in the small-to-moderate range.


### 1.6 Relative Predictive Strength Among Physical Attributes

Collectively, meta-analytic and longitudinal data suggest the following approximate ordering of physical attributes by predictive power for adult social and interpersonal outcomes (roughly from stronger to weaker within the physical domain):

- Height → social esteem, leadership, and income (ρ ≈ 0.2–0.4 for proximal social outcomes; β ≈ 0.26 for income).[2]
- Facial/overall attractiveness → positive evaluations, treatment, and some behavioral outcomes (d ≈ 0.20–0.37 across domains).[1][4]
- BMI/obesity and weight stigma → medium-to-large associations with mental health (r ≈ −0.35) and substantial discrimination in employment and social domains.[9][12]
- Chronic illness → high prevalence of social dysfunction and reduced quality of life, but effect sizes vary widely by condition.[15][16]
- Genital and body self-image → small-to-moderate associations with sexual function, relationship satisfaction, and psychological well-being.[26][17][21]


## 2. Childhood Experiences and Longitudinal Prediction of Adult Symptoms and Behavior

### 2.1 Adverse Childhood Experiences (ACEs)

Hughes et al. (2017, *The Lancet Public Health*) synthesized 37 studies (N ≈ 253,719) examining adults with multiple ACEs (e.g., abuse, neglect, household dysfunction) versus none.[27][28][29]
Compared with those reporting zero ACEs, individuals with four or more ACEs had:

- Odds ratios (ORs) > 7 for problematic drug use and interpersonal/self-directed violence.
- ORs > 3–6 for mental ill health, problematic alcohol use, and sexual risk behavior.
- ORs ≈ 2–3 for smoking, heavy alcohol use, poor self-rated health, cancer, heart disease, and respiratory disease.

The pattern indicates that cumulative ACE burden is one of the strongest longitudinal psychosocial predictors of a wide range of adult behavioral and health outcomes.


### 2.2 Childhood Sexual Abuse (CSA)

Multiple meta-analyses converge on small-to-moderate but pervasive effects of CSA on adult psychopathology.
Jumper (1995, *Child Abuse & Neglect*) meta-analyzed studies of CSA and adult adjustment and found significant relationships with psychological symptomatology, depression, and low self-esteem, with effect sizes typically in the small-to-moderate range.[30]
Irish et al. (2010, *Journal of Pediatric Psychology*) reviewed 31 studies and reported that CSA history was associated with small-to-moderate group differences across general health, gastrointestinal, gynecologic, pain, cardiopulmonary, and obesity outcomes.[31]

An umbrella review of meta-analyses on long-term outcomes of CSA similarly finds elevated risks for a wide range of psychiatric disorders, substance use, suicide attempts, and physical health conditions (Hailes et al., 2019, *World Psychiatry*).[32]
These effects are often non-specific (CSA increases risk for many outcomes rather than one specific syndrome) but substantive at the population level.


### 2.3 Attachment Quality in Early Life

Meta-analyses of attachment indicate moderate predictive validity for later social competence and smaller yet reliable effects on psychopathology.
Groh et al. (2014, *Attachment & Human Development*) synthesized 80 samples (N = 4,441) and found that early secure attachment is associated with better peer competence (d = 0.39) compared with insecure attachment.[33][34]
Avoidant, resistant, and disorganized attachment patterns each showed significant negative associations with peer competence (d ≈ 0.17–0.29).[33]

Fearon et al. (2010, *Child Development*) meta-analyzed 69 samples (N = 5,947) and found that attachment insecurity is associated with externalizing problems (d = 0.31 overall), with disorganized attachment showing somewhat higher risk (d ≈ 0.34) than avoidant or resistant patterns.[35][36]
A related meta-analysis of internalizing symptoms found smaller but significant effects (d ≈ 0.15 for insecurity overall; Groh et al., 2012, *Child Development*).[37]

These results position early attachment organization as a medium-sized predictor of social competence and a small-to-moderate predictor of later behavioral problems, especially externalizing.


### 2.4 Parental Loss and Separation

A systematic review and meta-analysis by Simbi, Zhang, and Wang (2020, *Journal of Affective Disorders*) examined early parental loss (death or separation before age 18) and adult depression.[38][39]
Across nine case–control studies (716 bereaved vs 2,068 controls), they reported:

- Any parental loss: OR = 2.18 (95% CI 1.63–2.90) for adult depression.
- Parental death: OR = 1.76 (95% CI 1.13–2.73).
- Parental separation: OR = 3.14 (95% CI 1.92–5.15).

Longitudinal work in the U.S. Add Health cohort shows that adolescents who lost a parent exhibit persistent deficits in developmental competence (work, peer relations, educational aspirations) years later (Brent et al., 2012, *Journal of Clinical Child & Adolescent Psychology*; Brent et al., 2016, *Death Studies*).[40][41]
However, some reviews note that when confounding variables are tightly controlled, the long-term effects of parental death on adult depression can be attenuated (e.g., Birtchnell, 1980, *Psychological Medicine*).[42]


### 2.5 Comparative Strength of Childhood Predictors

Synthesizing across domains, the strongest longitudinal childhood predictors of adult behavior and symptoms are:

- **Cumulative ACEs (4+ types)** → large ORs for violence, substance abuse, and mental illness.[27]
- **Specific severe maltreatment such as CSA** → small-to-moderate effects across many psychiatric and physical outcomes.[31][30][32]
- **Attachment disorganization/insecurity** → moderate effects on social competence (d ≈ 0.39 for security vs insecurity) and externalizing behavior (d ≈ 0.31).(Groh et al., 2014; Fearon et al., 2010).[35][33]
- **Parental separation or death** → roughly doubled to tripled odds of adult depression and measurable decrements in educational and economic trajectories, though estimates vary by cohort and control strategy.[38][40]


## 3. Korean Sociological Predictors Compared to Western Samples

### 3.1 University Rank and University Prestige

In South Korea’s stratified higher-education system, university rank exerts strong labor-market effects beyond individual ability.
Han, Bae, and Sohn (2012, *Korean Journal of Educational Policy*) used Korean Labor and Income Panel Study data and residual analyses to isolate a “prestige effect.”[43][44][45][46]
They estimated that attending Seoul National University (SNU) generates an earnings premium of about 12 percent over other universities, with SNU’s prestige effect more than twice that of Korea University and Yonsei University even after controlling for observable human-capital variables.

Other work on college quality in Korea similarly finds sizable wage premiums for elite private institutions compared with lower-ranked public colleges, suggesting that university rank is a strong positional variable in Korean life outcomes relative to many Western systems where institutional prestige effects, while present, are often smaller once selectivity and major are controlled.[47][48]


### 3.2 CSAT (Suneung) Scores and Labor-Market Outcomes

The College Scholastic Ability Test (CSAT, *Suneung*) functions as a central gatekeeper.
A study on supplemental education and labor-market performance (Kang, Lee, & Rhee, 2019, *Asian Economic Journal*) used standardized CSAT scores in wage equations and found that a one–standard deviation increase in CSAT score was associated with roughly an 8–9 percent increase in wages, even when controlling for education and experience.[49]

Korean Education Employment Panel (KEEP) analyses also show that CSAT scores strongly structure access to tiered universities, which in turn mediate returns to education, suggesting a multi-step pathway from CSAT → university quality → wages.[50]
Compared with Western contexts where standardized test scores predict educational attainment but have weaker *direct* effects on adult earnings once degree and institution are controlled, CSAT appears unusually central.


### 3.3 Appearance and Lookism

Appearance-based discrimination is particularly salient in Korea.
A longitudinal study of emerging adults found that perceived appearance discrimination (lookism) strongly predicted later poor self-rated health, with odds ratios for recurrent discrimination episodes around 3.7 for future poor health, even after controlling for baseline health and covariates (Yoon et al., 2017, *International Journal for Equity in Health*).[51][52]
Government surveys report that a majority of HR staff explicitly consider appearance in hiring decisions, and that 60 percent of firms require photographs with resumes, practices that persist despite anti-discrimination guidelines.[53][54]

Qualitative and survey work portrays lookism as an institutionalized stratification axis affecting employment opportunities, dating, and psychological well-being to a degree more intense than in most Western samples.[55][56]
In simulation terms, physical attractiveness/appearance may have a larger multiplier on employment and social integration probabilities for Korean agents than for Western agents with otherwise similar traits.


### 3.4 Parental Socioeconomic Status (SES) and Intergenerational Mobility

Analyses of Korean panel data indicate moderate intergenerational income persistence.
Nam (2017, *International Journal of Social Welfare*) estimated intergenerational income elasticity around 0.2, suggesting more mobility than in the U.S. or U.K., but still substantial parental influence.[57]
Korea Development Institute work using a parental SES index (income, education, occupational prestige) shows strong positive effects of parental SES on children’s educational attainment and early-career earnings.[58][59]

Compared with Western countries, Korean parental SES interacts strongly with education system stratification (hagwon use, elite high schools, CSAT prep), amplifying long-run outcome disparities.
Thus parental SES is a core predictor of life outcomes in both Korean and Western contexts, but in Korea it may be especially intertwined with university rank and CSAT.


### 3.5 Regional Background (Yeongnam vs Honam, Seoul vs Non-Seoul)

Historical accounts and journalistic analyses document persistent regional discrimination, particularly against people from the Honam region (Jeolla provinces), affecting hiring and promotion in politics and large firms.[60][61][62]
National Human Rights Commission surveys report that “people born in certain regions” are among the most frequent targets of hate speech, on- and offline.[63][64]
However, rigorous quantitative estimates of wage penalties or hiring odds by region are relatively scarce compared with evidence on university prestige and CSAT.

Regional background therefore appears to function as a significant qualitative stratifier in Korea—shaping social networks, political affiliation, and discrimination exposure—though its precise predictive strength relative to university rank and parental SES is less well quantified.


### 3.6 Relative Importance of Korean Variables

Within the Korean research context, the following ordering is supported by current data:

- **University rank / prestige (especially SKY)** → sizeable wage premiums (~10–15 percent) and strong signals in elite hiring.[43][47]
- **CSAT score** → strong predictor of university tier and direct wage effects (~8–9 percent per SD).[49]
- **Parental SES** → moderate-to-strong predictor of educational attainment and early-career status (elasticity ≈ 0.2; strong SES–education link).[57][58]
- **Appearance / lookism** → strong predictor of self-rated health and widely acknowledged factor in hiring and social evaluation; effect sizes on wages are less precisely quantified but likely non-trivial.[53][51]
- **Regional background** → clear evidence of discrimination, but limited standardized effect-size estimates.

Compared with Western samples, Korean sociology emphasizes institutional gatekeeping variables (CSAT, university rank, appearance) somewhat more heavily, while parental SES remains central in both contexts.


## 4. Trauma Research: Sensory Encoding and Adult Reactivation

### 4.1 Sensory-Dominant Nature of Traumatic Memories

Van der Kolk and Fisler (1995, *Journal of Traumatic Stress*) analyzed trauma narratives and proposed that early traumatic memories are initially stored as dissociated sensory and affective fragments—visual, olfactory, auditory, and kinesthetic impressions—rather than as integrated verbal narratives.[65][66]
Van der Kolk (1994, *Harvard Review of Psychiatry*) argued that trauma is often “stored in somatic memory,” with intrusive re-experiencing dominated by bodily sensations and vivid images rather than chronological stories.[67][68]

These accounts are consistent with neuroimaging findings showing decreased activation in language-related regions (e.g., Broca’s area) during trauma recall and heightened activation in limbic and sensory areas, supporting the idea that intrusive symptoms are strongly tied to sensory encoding channels.[65]


### 4.2 Olfactory and Other Sensory Triggers

Case series and reviews underscore the especial potency of olfactory cues.
Kline and Rausch (1985, *Journal of Clinical Psychiatry*) described vivid olfactory-triggered flashbacks in combat veterans with PTSD, arguing that smells can uniquely evoke intense reliving episodes.[69]
Vermetten and Bremner (2003, *Journal of Clinical Psychiatry*) reviewed cases where trauma-related smells (e.g., blood, burning, chemicals) served as primary precipitants of intrusive memories and panic, recommending routine assessment of olfactory triggers in PTSD.[70]

A broader review of odor-induced recall of emotional memories in PTSD (Daniels & Vermetten, 2016, *Experimental Neurology*) concluded that odor cues can elicit autobiographical memories that are more emotional than those triggered by visual or verbal cues, and that olfactory fear conditioning may contribute to persistent, cue-driven re-experiencing.[71][72]
These findings suggest that olfactory encoding during trauma confers particularly high risk for powerful, later reactivation.


### 4.3 Cognitive Models of Intrusive Sensory Memories

Ehlers and Clark’s cognitive model of PTSD (2000, *Behaviour Research and Therapy*) emphasizes that PTSD is maintained when trauma memories are poorly elaborated, strongly sensory-based, and easily triggered by cues, producing a persistent sense of current threat.[73][74]
They highlight features such as strong perceptual priming, lack of temporal context, and “hot spots” of sensory and emotional intensity as central to re-experiencing.
Empirical work from the same group shows that intrusive memories are often very brief, vivid sensory fragments rather than complete sequences, supporting the model.[75]


### 4.4 Polyvagal and Somatic Perspectives (Porges, Levine)

Porges’ Polyvagal Theory (2011, *The Polyvagal Theory*) conceptualizes trauma responses as shifts among autonomic states—ventral vagal (social engagement), sympathetic (fight/flight), and dorsal vagal (shutdown)—governed by “neuroception” of safety and threat.[76][77]
Trauma can leave individuals chronically biased toward sympathetic hyperarousal or dorsal shutdown, with physiological responses triggered by subtle sensory cues.

Levine’s Somatic Experiencing approach treats trauma as dysregulated survival energy “stuck” in the body’s procedural and interoceptive memory systems rather than in verbal narratives.[78][79][80]
His clinical framework assumes that tactile, proprioceptive, and interoceptive sensations related to the original trauma are central to adult reactivation, and that gradual titration of bodily experience can complete previously thwarted defensive responses.

Although these frameworks are less empirically quantified than cognitive models, they converge with van der Kolk’s findings on somatic/sensory memory and support the importance of bodily and autonomic cues in trauma reactivation.


### 4.5 Emotional Processing and Exposure (Foa and Colleagues)

Emotional Processing Theory (Foa & Kozak, 1986) posits that anxiety disorders, including PTSD, involve pathological fear structures in memory that can be modified through repeated, emotionally engaged exposure.[81]
Prolonged Exposure (PE) therapy, developed by Foa and colleagues, uses imaginal reliving of trauma narratives and in vivo exposure to avoided cues to promote habituation and cognitive restructuring.

PE’s effectiveness is supported by numerous trials; the APA recommends it as a first-line treatment.[82][83][84]
Recent work on PE process variables indicates that reductions in trauma-related negative thoughts and cognitive rigidity, rather than mere emotional activation, predict better outcomes (e.g., Levin et al., 2023, *Behaviour Research and Therapy*).[85]
This underscores the interaction between sensory reactivation and cognitive reinterpretation in symptom change.


### 4.6 Modalities Most Prone to Adult Reactivation

Integrating these perspectives, the sensory and experiential features most likely to produce adult reactivation symptoms include:

- **Olfactory cues** tied to the trauma (blood, burning, bodily fluids, specific environments) – repeatedly documented as particularly potent, often evoking intense, involuntary reliving.[70][71][69]
- **Highly salient visual “snapshots”** (e.g., particular facial expressions, weapons, injuries) – central to flashbacks described in cognitive and neurobiological accounts.[74][65]
- **Tactile/interoceptive sensations** (pressure, pain, suffocation, body position) – emphasized in somatic and polyvagal models, and often reported in trauma-related dissociative episodes.[67][78]
- **Coerced acts and humiliating behaviors** encoded with intense shame/fear – often reactivated by contextual, verbal, or bodily cues and strongly linked to avoidance, dissociation, and self-harm.[32][31]

For simulation design, modeling intrusive symptom propensity as a function of (a) sensory load at encoding (especially smell and body sensations), (b) peritraumatic dissociation, and (c) autonomic shutdown versus fight/flight state is consistent with these literatures.


## 5. Popular Personality/Type Variables with Low Predictive Validity

### 5.1 Myers–Briggs Type Indicator (MBTI)

Critical psychometric reviews conclude that MBTI has limited validity for predicting behavior or life outcomes.
Pittenger (1993, *Review of Educational Research*) reviewed MBTI research and found insufficient evidence to support key claims about its utility; he highlighted problems with categorical typing, unstable type assignments, and weak criterion validity.[86][87][88]
Later critiques similarly note that MBTI dimensions overlap with the Big Five but capture less variance and show weaker correlations with job performance and other external criteria.[89][90]

In contrast, Big Five traits such as conscientiousness show corrected validities around r ≈ 0.22–0.31 for job performance across many jobs (Barrick & Mount, 1991; Hurtz & Donovan, 2000).[91][92][93]
Thus, MBTI type categories have substantially lower predictive validity than trait-based models.


### 5.2 Enneagram

A systematic review of Enneagram research by Hook et al. (2021, *Journal of Clinical Psychology*) examined 104 independent samples and found mixed evidence for reliability and validity.[94][95]
Although some instruments show acceptable internal consistency and correlations with Big Five traits, factor-analytic work often yields fewer than nine factors, and there is *little to no published research* on Enneagram type predicting objective life outcomes (e.g., job performance, health, income).[96][97][94]

Recent technical and popular reviews explicitly acknowledge that the main gap is predictive validity: Enneagram types rarely explain incremental variance in outcomes beyond established trait measures.[98][99]
Accordingly, Enneagram categories should be treated as low-validity predictors in behavioral simulation compared with traits like conscientiousness or neuroticism.


### 5.3 Birth Order

Rohrer, Egloff, and Schmukle (2015, *PNAS*) used three large national panels (N ≈ 20,000 combined) from the U.S., U.K., and Germany and found that birth order has *no meaningful effect* on Big Five personality traits when siblings are compared within families, although firstborns show slightly higher intelligence and self-rated intellect.[100][101][102][103]
A PNAS commentary summarizing recent work concluded that mean birth-order effects on personality traits are effectively zero (r ≈ 0.00–0.02).[104]

Thus, while birth order may have small effects on cognitive measures, its predictive validity for broad personality and behavior is negligible in general populations.


### 5.4 Astrology and Zodiac Sign

Meta-analytic and experimental tests of astrology show that zodiac signs do not predict personality or behavior beyond chance.
A review of over 40 controlled studies concluded that astrologers were unable to predict personality more accurately than chance (Crowe, 1990, summarized in later experimental work on astrology and self-perception).[105]
Recent cross-cultural studies likewise find no significant correlations between zodiac sign and Big Five traits, with classification accuracy at chance levels (e.g., modern preprints and cross-national samples).[106][107]

Astrology’s apparent accuracy is instead explained by the Barnum/Forer effect and confirmation biases, not genuine predictive structure.[107][105]


### 5.5 Comparative Note

Compared with empirically grounded variables—general cognitive ability, Big Five traits, SES, ACEs—popular typologies (MBTI, Enneagram, birth order, astrology) either lack robust predictive validation or have been directly falsified as predictors of key behavioral outcomes.
In a simulation system, these should be assigned very low or zero weight for predicting objective behavior.


## 6. Ranked Variable Categories by Behavioral Predictive Power

The following table ranks broad variable categories by approximate predictive power for adult behavioral and life outcomes, based on meta-analytic effect sizes where available.
The ranking is approximate and domain-general (job performance, social functioning, health-risk behavior, and socioeconomic outcomes).

| Rank | Variable category (operationalization) | Typical meta-analytic effect size / association | Key domains predicted | Notes |
|------|---------------------------------------|-----------------------------------------------|------------------------|-------|
| 1 | Cumulative ACEs (number and severity of adverse childhood experiences) | OR > 7 for drug use and violence; OR > 3–6 for mental ill health and problematic alcohol use when ≥4 ACEs vs none (Hughes et al., 2017). | Adult mental disorders, substance use, violence, physical health. | Very strong, dose–response, multi-domain effects.[27][32] |
| 2 | Severe specific maltreatment (e.g., childhood sexual abuse) | Small-to-moderate effects (d ≈ 0.2–0.4) across many psychiatric and physical outcomes (Jumper, 1995; Irish et al., 2010; Hailes et al., 2019). | Depression, PTSD, suicidality, chronic health problems. | Non-specific risk factor affecting many outcome domains.[30][31][32] |
| 3 | Early attachment security/disorganization | d ≈ 0.39 for security vs insecurity and peer competence; d ≈ 0.31 for insecurity and externalizing problems (Groh et al., 2014; Fearon et al., 2010). | Childhood social competence, externalizing behavior, later relational patterns. | Moderate predictive power, especially for social functioning and aggression.[33][35][37] |
| 4 | General cognitive ability (GMA/IQ) | Corrected r ≈ 0.22–0.51 with job performance and training success depending on meta-analysis and corrections (Schmidt & Hunter, 1998; Salgado, 2019; Sackett et al., 2024). | Job performance, training, educational attainment, income. | Among the strongest individual-level predictors in occupational contexts.[108][109][110][111] |
| 5 | Personality traits: especially conscientiousness and (low) neuroticism | Conscientiousness: corrected r ≈ 0.22–0.31 with job performance; neuroticism and extraversion modest predictors in social/clinical domains (Barrick & Mount, 1991; Hurtz & Donovan, 2000). | Job performance, health behaviors, relationship stability, internalizing symptoms. | Trait-level predictors with robust but moderate effects.[91][92][93] |
| 6 | Parental SES / family-of-origin SES | Meta-analyses show medium SES–achievement correlations (r ≈ 0.25–0.31) in education; strong associations with adult income and health (Sirin, 2005; Zhao et al., 2024; APA factsheets). | Educational attainment, occupation, income, health. | In Korea, tightly linked with access to elite education and tutoring.[112][113][114][115][116] |
| 7 | Educational attainment / university rank (esp. SKY in Korea) | SNU prestige premium ≈ 12 percent vs other universities; elite college attendance associated with 10–17 percent wage premiums (Han et al., 2012; related Korean studies). | Earnings, occupational status, marriage market. | In Korea, university tier is an exceptionally strong positional signal.[43][47][45] |
| 8 | Standardized test scores (e.g., CSAT/Suneung in Korea) | 1 SD increase in CSAT associated with ~8–9 percent higher wages in Korea after controls (Kang et al., 2019). | University access, wages, occupational sorting. | Stronger direct economic impact in Korea than typical Western test-score effects.[49][50] |
| 9 | Physical height | ρ ≈ 0.41 with social esteem; ρ ≈ 0.24 with leader emergence; β ≈ 0.26 for income controlling covariates (Judge & Cable, 2004). | Leadership, income, occupational status. | Moderate predictor of status-related outcomes.[2][7] |
| 10 | Facial/overall attractiveness | d ≈ 0.20–0.30 for behavior/traits; d ≈ 0.37 for job-related outcomes (Langlois et al., 2000; Hosoda et al., 2003); longitudinal links to SES (Benzeval, 2013). | Social integration, romantic success, employment evaluations, SES. | In Korea, “lookism” likely amplifies these effects. |
| 11 | BMI/obesity and weight stigma | Weight stigma and mental health r ≈ −0.35; c

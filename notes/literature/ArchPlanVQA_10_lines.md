# ArchPlanVQA - 10-line note

Source: Crossref metadata for DOI 10.1061/JCCEE5.CPENG-7571, "ArchPlanVQA: Benchmark and Comprehensive Evaluation of Vision-Language Models for Understanding Architectural Floor Plan CAD Drawings".

1. ArchPlanVQA is the main first-week pointer for evaluating general VLMs on architectural floor-plan CAD drawings.
2. It matters because DrawingPT must test VLM baselines rather than only quoting that VLMs are weak.
3. The task format is VQA, so it probes visual-language reasoning over drawings instead of pure detection or segmentation.
4. Use it to design questions that stress precise engineering reasoning: counting, measurement, spatial relation, symbol recognition, and text-grounded answers.
5. For a fair VLM comparison, freeze rendering resolution, crop policy, prompt template, answer format, and scoring script before running models.
6. VLM metrics should be separated by answer type: exact match for categories, numeric tolerance for counts/measurements, and human/rubric checks only when unavoidable.
7. ArchPlanVQA does not replace FloorPlanCAD panoptic symbol spotting; it is a complementary evaluation for the raster/VLM route.
8. DrawingPT should report both strengths and failures of VLMs; the red-line claim is vector-native sample efficiency and auditability, not "VLMs are useless".
9. If using proprietary VLM APIs later, record model version, date, prompt, image preprocessing, and cost because the results are time-sensitive.
10. Next action: keep an ArchPlanVQA-style prompt suite as a week-7/8 comparison once the vector baseline and DrawingPT v0 are stable.

# Experiments

Record every run here before copying final summaries into the paper notes.

Minimum fields for a baseline run:

- Date
- Git commit
- Dataset version and split
- Hardware
- Command
- Runtime
- Metrics
- Gap from reported paper number
- Failure notes

The key DrawingPT acceptance plot is the week-6 label-efficiency curve:

- x-axis: number or fraction of labeled drawings
- y-axis: downstream performance
- curves: pre-trained vs trained from scratch
- stop-loss rule: pause and diagnose if relative gain is below 5%


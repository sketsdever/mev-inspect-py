from mev_inspect.schemas.traces import Classification
from mev_inspect.classifiers.trace import TraceClassifier
from tests.utils import load_test_block

def test_identifiying_new_markets():
    # MKR was added to COMP in this block
    block_number = 12949662
    block = load_test_block(block_number)
    trace_classifier = TraceClassifier()
    classified_traces = trace_classifier.classify(block.traces)
    has_new_market = False
    for trace in classified_traces:
        if(trace.classification == Classification.new_market and trace.inputs['cToken'] == '0x95b4ef2869ebd94beb4eee400a99824bf5dc325b'):
            has_new_market = True
    assert has_new_market == True


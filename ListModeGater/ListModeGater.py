import numpy as np
import argparse
from ListModeGater import timing 
from ListModeGater import listmodereader as lmr

def main():
    parser = argparse.ArgumentParser() 
    parser.add_argument("--input_cdh", help="Path to data header file", required=True)
    parser.add_argument("--input_cdf", help="Path to data binary file", required=True)
    parser.add_argument("--frm", help="Framing information", required=True)
    parser.add_argument("--tags", help="Respiratory Tag information", required=True)
    parser.add_argument("--nb_gates", help="Number of gates", required=True, type=int)
    args = parser.parse_args()

    framing = timing.FrameConverter(args.frm)
    gates = timing.GatingTags(args.tags,args.nb_gates)
    gates.make_gate_info()

    _,last_time_tag = lmr.listmodereader("IffffII",args.input_cdf)
    gates.make_Info_Matrix(last_time_tag,framing.FrameStart,framing.FrameDuration)

    _, data_sizes, frame_stats = lmr.listmodewriter("IffffII",args.input_cdf,args.input_cdh,gates,framing.nbFrames)

    timing_ratios = gates.get_timing_ratios()

    lmr.listmodecorrector(args.input_cdf, "IffffII", timing_ratios)

    lmr.listmodeheaderwriter(args.input_cdh, data_sizes, timing_ratios)
    
    print("For each frame, the number of events in each gate:")
    for frame in range(framing.nbFrames):
        print("Frame ",frame," : ",frame_stats[frame,:])

    print("Done")

if __name__ == "__main__":
    main()


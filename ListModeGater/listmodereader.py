import struct
import os
import numpy as np
from ListModeGater import timing


def listmodecorrector(datafile: str, bitstructure: str, timing_ratios) -> None:
    size = struct.calcsize(bitstructure)
    single_gate_files = [ os.path.basename(datafile).split('.')[0]+'_Single_GATE_temporaire_'+str(gate)+'.cdf' for gate in range(len(timing_ratios)) ]
    correc_gate_files = [ open(os.path.basename(datafile).split('.')[0]+'_Single_GATE_'+str(gate)+'.cdf', "wb") for gate in range(len(timing_ratios)) ]
    for idx in range(len(timing_ratios)):
        with open(single_gate_files[idx], mode='rb') as file: # b is important -> binary
            datafilePack = file.read(size)
            while datafilePack:
                unpacked = struct.unpack(bitstructure,datafilePack)
                unpacked = list(unpacked)
                unpacked[2] =  unpacked[2]*timing_ratios[idx]
                unpacked[3] =  unpacked[3]*timing_ratios[idx]
                packet = struct.pack(bitstructure,*unpacked)
                correc_gate_files[idx].write(packet)
                datafilePack = file.read(size)

def listmodeheaderwriter(dataheader: str, data_sizes: list, timing_ratios: list) -> None:
    # copy the header as is for the gated file, just by changing the file name
    with open(dataheader, mode='r') as file: # b is important -> binary
        data = file.readlines()
        for idx,line in enumerate(data): 
            if "Data filename:" in line:
                data[idx] = "Data filename: "+os.path.basename(dataheader).split('.')[0]+'_GATED.cdf'+"\n"
    new_header = os.path.basename(dataheader).split('.')[0]+'_GATED.cdh'
    with open(new_header, 'w') as file:
        file.writelines( data )

    # create a new header for each single gate file
    for gate in range(len(data_sizes)):
        with open(dataheader, mode='r') as file: # b is important -> binary
            data = file.readlines()
            for idx,line in enumerate(data): 
                if "Data filename:" in line:
                    data[idx] = "Data filename: "+os.path.basename(dataheader).split('.')[0]+'_Single_GATE_'+str(gate)+'.cdf'+"\n"
                if "Number of events" in line:
                    data[idx] = "Number of events: "+str(data_sizes[gate])+"\n"
                if "Calibration factor:" in line:
                    cal_factor = float(data[idx].split(":")[1])
                    cal_factor = cal_factor/timing_ratios[gate]
                    data[idx] = f"Calibration factor: "+str(cal_factor)+'\n'
        new_header = os.path.basename(dataheader).split('.')[0]+'_Single_GATE_'+str(gate)+'.cdh'
        with open(new_header, 'w') as file:
            file.writelines( data )

def listmodereader(bitstructure: str, datafile: str) -> None:
    size = struct.calcsize(bitstructure)
    with open(datafile, mode='rb') as file: # b is important -> binary
        datafilePack = file.read(size)
        # read its time tag , as the first time tag
        firstTimeTag = int(struct.unpack("I",datafilePack[:4])[0])
        file.seek(os.path.getsize(datafile)-size)
        # Read last phrase
        datafilePack = file.read(size)
        # read its time tag , as the last time tag
        lastTimeTag = int(struct.unpack("I",datafilePack[:4])[0])

    return(firstTimeTag,lastTimeTag)


def listmodewriter(bitstructure: str, datafile: str, dataheader: str, gates: timing.GatingTags, nbFrames: int) -> list:
    size = struct.calcsize(bitstructure)
    frame_stats = np.zeros([nbFrames,gates.nb_gates],dtype=np.int32)
    with open(datafile, mode='rb') as file: # b is important -> binary
        GATEDFile = open(os.path.basename(datafile).split('.')[0]+'_GATED.cdf', "wb")
        gate_buffers = [ [] for _ in range(gates.nb_gates) ]
        single_gate_buffers = [ [] for _ in range(gates.nb_gates) ]
        single_gate_files = [ open(os.path.basename(datafile).split('.')[0]+'_Single_GATE_temporaire_'+str(gate)+'.cdf', "wb") for gate in range(gates.nb_gates) ]

        # Read first datafilePack
        datafilePack = file.read(size)
        count=1
        TotaldataCount=0
        GateCounts = [0 for _ in range(gates.nb_gates)]
        cur_frame=-1
        # Loop over all data untill end of file
        while datafilePack:
            # get time tag
            timetag = int(struct.unpack("I",datafilePack[:4])[0])
            # Check if we will use this time tag
            if gates.InfoMatrix[timetag,2]>-1:
                if gates.InfoMatrix[timetag,2] > cur_frame:
                    cur_frame+=1
                    # Write the 5 gates
                    for gate in range(gates.nb_gates):
                        GATEDFile.write(bytearray(gate_buffers[gate]))
                        gate_buffers[gate] = []

                count+=1
                for gate in range(gates.nb_gates):
                    if gates.InfoMatrix[timetag,3]==gate:
                        frame_stats[cur_frame,gate]+=1
                        TotaldataCount+=1
                        gate_buffers[gate].extend(datafilePack)
                        GateCounts[gate]+=1
                        single_gate_buffers[gate].extend(datafilePack)

            # Read next datafilePack
            datafilePack = file.read(size)


        # Write the last 5 gates
        for gate in range(gates.nb_gates):
            GATEDFile.write(bytearray(gate_buffers[gate]))
            #gate_buffers[gate] = []

        # Write the single gate files 
        for gate in range(gates.nb_gates):
            single_gate_files[gate].write(bytearray(single_gate_buffers[gate]))
            #single_gate_buffers[gate] = []
            single_gate_files[gate].close()
        
        GATEDFile.close() 
        for single_gate_file in single_gate_files: single_gate_file.close()

        data_sizes = [GateCounts[gate] for gate in range(gates.nb_gates)]

        data_ratios = [GateCounts[gate]/TotaldataCount for gate in range(gates.nb_gates)]
        return data_ratios, data_sizes, frame_stats


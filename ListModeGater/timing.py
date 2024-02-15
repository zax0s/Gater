import numpy as np

class GatingTags:
    def __init__(self, tagtext,nb_gates):
        
        self.nb_triggers = len(tagtext.split(","))
        self.resp_triggers = [int(i) for i in tagtext.split(",")]

        self.nb_gates = nb_gates
        self.nb_splits = (nb_gates -1)*2

    def make_gate_info(self):
        np.concatenate([np.arange(self.nb_gates), np.arange(self.nb_gates-2,0,-1)])
        self.gate_infos = np.zeros([self.nb_triggers-1,self.nb_splits,2],dtype=np.int32)

        for idx,_ in enumerate(self.resp_triggers [:-1]):
            diff = (self.resp_triggers [idx+1]-self.resp_triggers [idx])
            for gate in range(self.nb_splits):
                gate_start = self.resp_triggers [idx]+diff*gate/8
                gate_end = self.resp_triggers [idx]+diff*(gate+1)/8
                gate_start-=diff/(self.nb_splits*2)
                gate_end-=diff/(self.nb_splits*2)
                self.gate_infos[idx,gate,0] = gate_start
                self.gate_infos[idx,gate,1] = gate_end

    def make_Info_Matrix(self,last_time_tag, FrameStart,FrameDuration):
        sequence = np.concatenate([np.arange(self.nb_gates), np.arange(self.nb_gates-2,0,-1)])
        current_resp_cycle=0
        current_frame=0
        #0: time-tag
        #1: respiratory cycle index
        #2: Frame index
        #3: Gate index
        #4: Phase within the respiratory cycle
        self.InfoMatrix = np.zeros([last_time_tag+1,5],dtype=np.int32)
        self.InfoMatrix[:,0] = np.arange(last_time_tag+1)
        #initialize the frame column with -1
        self.InfoMatrix[:,2] = -1

        for tag in (range(self.resp_triggers[0],self.resp_triggers[-1])):
            # Check if we need to update frame index
            if tag>=((FrameStart[current_frame]+FrameDuration[current_frame])*1000):
                current_frame+=1;
            self.InfoMatrix[tag,2]=current_frame
            # it tag is greater or equal to the following resp trigger, move one cycle up
            if tag>=self.resp_triggers[current_resp_cycle+1]:
                current_resp_cycle+=1;
            self.InfoMatrix[tag,1]=current_resp_cycle
            # we splitt the data in the resp cycle in 5 parts/gates for Q.Static data   
            for gate in range(self.nb_splits):
                gate_start=self.gate_infos[current_resp_cycle,gate,0]
                gate_end=self.gate_infos[current_resp_cycle,gate,1]
                if (gate_start<=tag<gate_end):
                    self.InfoMatrix[tag,3]=sequence[gate]
                    self.InfoMatrix[tag,4]=gate
        # write the info matrix to a file
        np.savetxt("InfoMatrix.csv",self.InfoMatrix[self.InfoMatrix[:,2]>-1],delimiter=",",fmt='%i')

    def get_timing_ratios(self):
        stat_cnts = [ [] for _ in range(self.nb_gates) ]
        CleanInfoMatrix = self.InfoMatrix[self.InfoMatrix[:,2]>-1]
        # The stats in each gate represent the milliseconds in each gate
        for gate in range(self.nb_gates):
            stat_cnts[gate] = np.sum(CleanInfoMatrix[:,3]==gate)
        stat_cnts = np.array(stat_cnts)
        return stat_cnts/np.sum(stat_cnts)

class FrameConverter:
    def __init__(self, frmtext):
        self.frames_phrases = frmtext.split(",")
        self.nbFrames = len(self.frames_phrases)
        self.FrameStart = np.zeros(self.nbFrames)
        self.FrameDuration = np.zeros([len(self.frames_phrases)])
        self.FrameStop = np.zeros([len(self.frames_phrases)])
        self.fr = 0
        self.set_frames()

    def set_frames(self):
        for phrase in self.frames_phrases:
            if phrase.find(":") != -1:
                self.FrameStart[self.fr] = float(phrase.split(":")[0])
                self.FrameDuration[self.fr] = float(phrase.split(":")[1])
            else:
                self.FrameStart[self.fr] = float(phrase)
            self.fr += 1

        for idx, val in enumerate(self.FrameDuration):
            if val == 0:
                self.FrameDuration[idx] = self.FrameStart[idx + 1] - self.FrameStart[idx]
            self.FrameStop[idx] = self.FrameStart[idx] + self.FrameDuration[idx]

        for idx in range(self.nbFrames-1):
            if self.FrameStart[idx+1] == 0:
                self.FrameStart[idx+1] = self.FrameStart[idx] + self.FrameDuration[idx]
        for idx in range(self.nbFrames):
            self.FrameStop[idx] = self.FrameStart[idx] + self.FrameDuration[idx]

        self.FrameDuration = self.FrameDuration.astype(np.int32)
        self.FrameStart = self.FrameStart.astype(np.int32)
        self.FrameStop = self.FrameStop.astype(np.int32)
        self.nbFrames = self.nbFrames


    
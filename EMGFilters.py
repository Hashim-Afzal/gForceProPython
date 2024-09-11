#!/usr/bin/python3
# -*- coding:utf-8 -*-

from enum import Enum

# coefficients of transfer function of LPF
# coef[sampleFreqInd][order]
lpf_numerator_coef = [[0.3913, 0.7827, 0.3913], [0.1311, 0.2622, 0.1311]]
lpf_denominator_coef = [[0.3913, 0.7827, 0.3913], [1.0000, -0.7478, 0.2722]]

# coefficients of transfer function of HPF
hpf_numerator_coef = [[0.8371, -1.6742, 0.8371], [0.9150, -1.8299, 0.9150]]
hpf_denominator_coef = [[1.0000, -1.6475, 0.7009], [1.0000, -1.8227, 0.8372]]

# coefficients of transfer function of anti-hum filter
# coef[sampleFreqInd][order] for 50Hz
ahf_numerator_coef_50Hz = [[0.9522, -1.5407, 0.9522, 0.8158, -0.8045, 0.0855], [0.5869, -1.1146, 0.5869, 1.0499, -2.0000, 1.0499]]
ahf_denominator_coef_50Hz = [[1.0000, -1.5395, 0.9056, 1.0000, -1.1187, 0.3129], [1.0000, -1.8844, 0.9893, 1.0000, -1.8991, 0.9892]]
ahf_output_gain_coef_50Hz = [1.3422, 1.4399]
# coef[sampleFreqInd][order] for 60Hz
ahf_numerator_coef_60Hz = [[0.9528, -1.3891, 0.9528, 0.8272, -0.7225, 0.0264], [0.5824, -1.0810, 0.5824, 1.0736, -2.0000, 1.0736]]
ahf_denominator_coef_60Hz = [[1.0000, -1.3880, 0.9066, 1.0000, -0.9739, 0.2371], [1.0000, -1.8407, 0.9894, 1.0000, -1.8584, 0.9891]]
ahf_output_gain_coef_60Hz = [1.3430, 1.4206]


SAMPLE_FREQ_500HZ = 500
SAMPLE_FREQ_1000HZ = 1000

NOTCH_FREQ_50HZ = 50
NOTCH_FREQ_60HZ = 60

class FILTER_TYPE(Enum):

    FILTER_TYPE_LOWPASS = 0
    FILTER_TYPE_HIGHPASS = 1

class FILTER_2nd:
    # second-order filter

    def __init__(self, ftype: FILTER_TYPE , sampleFreq: int):
        self.states = [0]*2
        self.num = [0]*3
        self.den = [0]*3
        if (ftype == FILTER_TYPE.FILTER_TYPE_LOWPASS):
            # 2th order butterworth lowpass filter
            # cutoff frequency 150Hz
            if (sampleFreq == SAMPLE_FREQ_500HZ):
                self.num = lpf_numerator_coef[0]
                self.den = lpf_denominator_coef[0]
            elif (sampleFreq == SAMPLE_FREQ_1000HZ):
                self.num = lpf_numerator_coef[1]
                self.den = lpf_denominator_coef[1]

        elif (ftype == FILTER_TYPE.FILTER_TYPE_HIGHPASS):
            # 2th order butterworth
            # cutoff frequency 20Hz
            if (sampleFreq == SAMPLE_FREQ_500HZ):
                self.num = hpf_numerator_coef[0]
                self.den = hpf_denominator_coef[0]

            elif (sampleFreq == SAMPLE_FREQ_1000HZ):
                self.num = hpf_numerator_coef[1]
                self.den = hpf_denominator_coef[1]

        print("num", self.num)
        print("den", self.den)
        

    def update(self, inp: float) -> float:
        tmp = (inp - self.den[1] * self.states[0] - self.den[2] * self.states[1]) / self.den[0]
        output = self.num[0] * tmp + self.num[1] * self.states[0] + self.num[2] * self.states[1]
        # save last states

        self.states[1] = self.states[0]
        self.states[0] = tmp
        print(self.states)
        return output

class FILTER_4th:
    # fourth-order filter
    # cascade two 2nd-order filters

    def __init__(self, sampleFreq: int, humFreq: int):
        self.states = [0]*4
        self.num = [0]*6
        self.den = [0]*6
        self.gain = 0
        if (humFreq == NOTCH_FREQ_50HZ):
            if (sampleFreq == SAMPLE_FREQ_500HZ):
                self.num = ahf_numerator_coef_50Hz[0]
                self.den = ahf_denominator_coef_50Hz[0]
                self.gain = ahf_output_gain_coef_50Hz[0]

            elif (sampleFreq == SAMPLE_FREQ_1000HZ):
                self.num = ahf_numerator_coef_50Hz[1]
                self.den = ahf_denominator_coef_50Hz[1]
                self.gain = ahf_output_gain_coef_50Hz[1]
        elif (humFreq == NOTCH_FREQ_60HZ):
            if (sampleFreq == SAMPLE_FREQ_500HZ):
                self.num = ahf_numerator_coef_60Hz[0]
                self.den = ahf_denominator_coef_60Hz[0]
                self.gain = ahf_output_gain_coef_60Hz[0]

            elif (sampleFreq == SAMPLE_FREQ_1000HZ):
                self.num = ahf_numerator_coef_60Hz[1]
                self.den = ahf_denominator_coef_60Hz[1]
                self.gain = ahf_output_gain_coef_60Hz[1]
        # print(self.states, self.num, self.den)

    def update(self, inp: float) -> float:
        output = None
        stageIn = None
        stageOut = None

        stageOut  = self.num[0] * inp + self.states[0]
        self.states[0] = (self.num[1] * inp + self.states[1]) - self.den[1] * stageOut
        self.states[1] = self.num[2] * inp - self.den[2] * stageOut
        stageIn   = stageOut
        stageOut  = self.num[3] * stageOut + self.states[2]
        self.states[2] = (self.num[4] * stageIn + self.states[3]) - self.den[4] * stageOut
        self.states[3] = self.num[5] * stageIn - self.den[5] * stageOut

        output = self.gain * stageOut

        return output


class EMGFilter:

    # LPF = None
    # HPF = None
    # AHF = None
    # m_sampleFreq   = None
    # m_notchFreq    = None
    # m_bypassEnabled = None
    # m_notchFilterEnabled    = None
    # m_lowpassFilterEnabled  = None
    # m_highpassFilterEnabled = None

    def  __init__(self, sampleFreq, notchFreq, enableNotchFilter, enableLowpassFilter, enableHighpassFilter):
        self.m_sampleFreq   = sampleFreq
        self.m_notchFreq    = notchFreq
        self.m_bypassEnabled = True
        if (((sampleFreq == SAMPLE_FREQ_500HZ) or (sampleFreq == SAMPLE_FREQ_1000HZ)) and
            ((notchFreq == NOTCH_FREQ_50HZ) or (notchFreq == NOTCH_FREQ_60HZ))):
            self.m_bypassEnabled = False

        self.LPF = FILTER_2nd(FILTER_TYPE.FILTER_TYPE_LOWPASS, self.m_sampleFreq)
        self.HPF = FILTER_2nd(FILTER_TYPE.FILTER_TYPE_HIGHPASS, self.m_sampleFreq)
        self.AHF = FILTER_4th(self.m_sampleFreq, self.m_notchFreq)

        self.m_notchFilterEnabled    = enableNotchFilter
        self.m_lowpassFilterEnabled  = enableLowpassFilter
        self.m_highpassFilterEnabled = enableHighpassFilter

    def update(self, inputValue: int) -> int:
        output = 0
        if (self.m_bypassEnabled):
            output = inputValue
            return output

        # first notch filter
        if (self.m_notchFilterEnabled):
            # output = NTF.update(inputValue)
            output = self.AHF.update(inputValue)
        else:
            # notch filter bypass
            output = inputValue

        # second low pass filter
        if (self.m_lowpassFilterEnabled):
            output = self.LPF.update(output)
        
        # third high pass filter
        if (self.m_highpassFilterEnabled):
            output = self.HPF.update(output)

        return output

if __name__ == "__main__":
    emgfilter = EMGFilter(SAMPLE_FREQ_500HZ, NOTCH_FREQ_50HZ, True, True, False)
    # test_values = [[125, 123, 117, 118, 117, 120, 130, 125], [123, 125, 122, 123, 118, 121, 130, 128]]
    # test_values = [125, 123, 126, 111, 115, 126, 125, 108, 120, 128, 129, 121, 120, 124, 125, 112]
    test_values = [125, 123, 126, 111, 115, 126, 125, 108, 120, 128, 129, 121, 120, 124, 125, 112, 109, 124, 123, 122, 114, 114, 124, 133, 125, 101, 119, 123, 126, 126, 116, 111, 128, 123, 132, 134, 115, 100, 114, 131, 124, 131, 119, 120, 117, 115, 121, 121, 124, 121, 120, 117, 123, 124, 117, 122, 119, 121, 120, 119, 116, 125, 125, 113, 121, 126, 127, 114, 114, 115, 123, 116, 126, 126, 117, 116, 132, 121, 117, 123, 116, 115, 116, 129, 123, 121, 118, 114, 125, 114, 113, 126, 125, 125, 119, 116, 115, 127, 125, 122]
    filtered_test = []
    for row in test_values:
        temp = []
        temp.append(emgfilter.update(row))
        filtered_test.append(temp)

    for i in range(5):
        print(test_values[i], filtered_test[i])

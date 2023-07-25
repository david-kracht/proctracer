from matplotlib import pyplot as plt
import copy
from plugin_proc_tracer_base import ProcTracerBase

US_IN_SECOND = 0.000001

class pressure_cpu(ProcTracerBase):

    def __init__(self,config_yaml):
        super().__init__(
            config_yaml=config_yaml,
            file='/proc/pressure/cpu',
            key='kpi',
            header_in='kpi avg10 avg60 avg300 total',
            )

    def mapper(self, sample):
        new_sample={}

        for k,entry in sample.items():
            new_sample[k] = {
                self.key : entry[self.key],
                'time': entry['time'],
                'avg10': float(entry['avg10'].split("=")[1]) ,
                'avg60': float(entry['avg60'].split("=")[1]) ,
                'avg300': float(entry['avg300'].split("=")[1]) ,
                'total': float(entry['total'].split("=")[1]) ,
                'avgTs': 0.0 ,
                }
            
            #use last sample for current value
            if k in self.sample_old:
                new_sample[k]['avgTs'] = 100.0 * ( new_sample[k]['total'] - self.sample_old[k]['total'] ) * US_IN_SECOND / ( new_sample[k]['time'] - self.sample_old[k]['time'] )

            
        return new_sample

    def add_diagrams(self, pdf, maxT):


        plt.clf()
        # Creating figure
        cm = 1/2.54                                         # centimeters in inches
        fig, axs = plt.subplots(2, dpi=72, figsize=(29.7*cm,21.0*cm))   # for landscape DIN A4

        fig.suptitle('%s' % self.file )

        if not self.data_frame.empty:
        
            del self.data_frame['total']
            
            pivot_table = self.data_frame.pivot_table(index='time', columns=[self.key])

            x=pivot_table.xs(axis=1, level=1, key="some")
            
            axs[0].plot(x, label= (x.columns if len(x.columns)>1 else x.columns[0]) )
            axs[0].legend(title="some", fontsize='small', loc= 'upper right')
            axs[0].set_ylabel('Some Stall Time [%]')
            axs[0].grid()
            axs[0].set_xlim(0,maxT)
            axs[0].set_ylim(0,105.0)

            x=pivot_table.xs(axis=1, level=1, key="full")

            axs[1].plot(x, label=(x.columns if len(x.columns)>1 else x.columns[0]))
            axs[1].legend(title="full", fontsize='small', loc= 'upper right')        
            axs[1].set_xlabel('Time t [s]')
            axs[1].set_ylabel('Full Stall Time [%]')
            axs[1].grid()
            axs[1].set_xlim(0,maxT)
            axs[1].set_ylim(0,105.0)

        pdf.savefig(fig)


class pressure_io(pressure_cpu):
    def __init__(self,config_yaml):
        super().__init__(config_yaml=config_yaml)
        self.file='/proc/pressure/io'

class pressure_memory(pressure_cpu):
    def __init__(self,config_yaml):
        super().__init__(config_yaml=config_yaml)
        self.file='/proc/pressure/memory'
from matplotlib import pyplot as plt

from plugin_proc_tracer_base import ProcTracerBase

class stat(ProcTracerBase):

    def __init__(self,config_yaml):
        super().__init__(
            config_yaml=config_yaml,
            file='/proc/stat',
            key='cpu',
            header_in='cpu user nice system idle iowait irq softirq steal guest guest_nice',
            first_line=0,
            patterns='cpu'
            )

    def mapper(self, sample):

        #reduce information stored (new sample)
        new_sample={}

        for k,entry in sample.items():
            new_sample[k] = {
                self.key : k,
                'time': entry['time'],
                'idle': int(entry['idle']),
                'total': sum([int(entry[i]) for i in 'user nice system idle iowait irq softirq steal guest guest_nice'.split() ]) ,
                'load' : 0.0,
                 }

            #use last sample for current value
            if k in self.sample_old:
                if (new_sample[k]['total']-self.sample_old[k]['total']) != 0:
                    new_sample[k]['load'] = ( 1.0 - ( new_sample[k]['idle']-self.sample_old[k]['idle'] ) / ( new_sample[k]['total']-self.sample_old[k]['total'] ) )

        return new_sample

    def add_diagrams(self, pdf, maxT):

        plt.clf()

        # Creating figure
        cm = 1/2.54                                                     # inches per centimeters
        fig, axs = plt.subplots(2, dpi=72, figsize=(29.7*cm,21.0*cm))   # for landscape DIN A4

        fig.suptitle('%s' % self.file )

        if not self.data_frame.empty:

            pivot_table = self.data_frame.pivot_table(index='time', columns=[self.key], values='load')

            ######### Overall
            axs[0].plot( pivot_table[['cpu']].dropna() *100, label='cpu' )
            axs[0].legend(fontsize='small', loc= 'upper right')
            axs[0].set_ylabel('CPU Load [%]')
            axs[0].grid()
            axs[0].set_xlim(0,maxT)
            axs[0].set_ylim(0,105.0)

            ######### Isolated
            for i in pivot_table.columns:
                if i != 'cpu':
                    axs[1].plot( pivot_table[[i]].dropna() *100, label=i )

            axs[1].legend(fontsize='small', loc= 'upper right')
            axs[1].set_xlabel('Time t [s]')
            axs[1].set_ylabel('CPU Loads [%]')
            axs[1].grid()
            axs[1].set_xlim(0,maxT)
            axs[1].set_ylim(0,105.0)

        pdf.savefig(fig)
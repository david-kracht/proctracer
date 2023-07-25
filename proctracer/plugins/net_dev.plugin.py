from matplotlib import pyplot as plt

from plugin_proc_tracer_base import ProcTracerBase

class net_dev(ProcTracerBase):

    def __init__(self, config_yaml):
        super().__init__(
            config_yaml=config_yaml,
            file='/proc/net/dev',
            key='interface',
            header_in='interface rx-bytes rx-packets rx-errs rx-drop rx-fifo rx-frame rx-compressed rx-multicast tx-bytes tx-packets tx-errs tx-drop tx-fifo tx-colls tx-carrier tx-compressed',
            first_line=2,
            patterns='eth ens enp lo'
            )

    def mapper(self, sample):
        new_sample={}
        for k,entry in sample.items():
            new_sample[k] = {
                self.key : k,
                'time': entry['time'],
                'rx-bytes': int(entry['rx-bytes']),
                'rx-packets': int(entry['rx-packets']),
                'tx-bytes': int(entry['tx-bytes']),
                'tx-packets': int(entry['tx-packets']),
                
                'rx-bytes-per-sec': 0.0,
                'rx-packets-per-sec': 0.0,
                'tx-bytes-per-sec': 0.0,
                'tx-packets-per-sec': 0.0,
                 }
                 
            if k in self.sample_old:
                new_sample[k]['rx-bytes-per-sec'] = ( new_sample[k]['rx-bytes'] - self.sample_old[k]['rx-bytes'] ) / ( new_sample[k]['time'] - self.sample_old[k]['time'] )
                new_sample[k]['rx-packets-per-sec'] = ( new_sample[k]['rx-packets'] - self.sample_old[k]['rx-packets'] ) / ( new_sample[k]['time'] - self.sample_old[k]['time'] )
                new_sample[k]['tx-bytes-per-sec'] = ( new_sample[k]['tx-bytes'] - self.sample_old[k]['tx-bytes'] ) / ( new_sample[k]['time'] - self.sample_old[k]['time'] )
                new_sample[k]['tx-packets-per-sec'] = ( new_sample[k]['tx-packets'] - self.sample_old[k]['tx-packets'] ) / ( new_sample[k]['time'] - self.sample_old[k]['time'] )
                

        return new_sample

    def add_diagrams(self, pdf, maxT):

        plt.clf()

        # Creating figure
        cm = 1/2.54                                                     # inches per centimeters
        fig, axs = plt.subplots(2, dpi=72, figsize=(29.7*cm,21.0*cm))   # for landscape DIN A4

        fig.suptitle('%s' % self.file )

        if not self.data_frame.empty:

            ######### Bytes
            for value in ['rx-bytes-per-sec', 'tx-bytes-per-sec']:

                pivot_table = self.data_frame.pivot_table(index='time', columns=[self.key], values=value)
                pivot_table = pivot_table.loc[:, (pivot_table > 0).any()]        
            
                for i in pivot_table.columns:
                    axs[0].plot( pivot_table[[i]].dropna(), label="%s %s" % (i, value ) )
            
            if not pivot_table.columns.empty:
                axs[0].legend(title="interface: [tx,rx]", fontsize='small', loc= 'upper right')
                
            axs[0].set_ylabel('Byte-Rate [1/s]')
            axs[0].grid()
            axs[0].set_xlim(0,maxT)
            axs[0].set_ylim(0,None)

            ######### Packets
            for value in ['rx-packets-per-sec', 'tx-packets-per-sec']:
                pivot_table = self.data_frame.pivot_table(index='time', columns=[self.key], values=value)
                pivot_table = pivot_table.loc[:, (pivot_table > 0).any()]
                
                for i in pivot_table.columns:
                    axs[1].plot( pivot_table[[i]].dropna(), label="%s %s" % (i, value ) )

            axs[1].set_xlabel('Time t [s]')
            axs[1].set_ylabel('Packet-Rate [1/s]')
            axs[1].grid()
            axs[1].set_xlim(0,maxT)
            axs[1].set_ylim(0,None)

        pdf.savefig(fig)
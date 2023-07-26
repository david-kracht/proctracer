from matplotlib import pyplot as plt

from plugin_proc_tracer_base import ProcTracerBase

class net_udp4(ProcTracerBase):

    def __init__(self,config_yaml):
        super().__init__(
            config_yaml=config_yaml,
            file='/proc/net/udp',
            key='inode',
            header_in='sl local_address rem_address st tx_queue:rx_queue tr:tm->when retrnsmt uid timeout inode ref pointer drops',
            first_line=1,
            patterns=''
            )
        
    def convert_hex_socket(self, hex_socket):
        h_addr, h_port = hex_socket.split(':')
        h_addr_list = ["".join(x) for x in zip(*[iter(str(h_addr))]*2)]
        d_addr_list = [int(x, 16) for x in h_addr_list]
        d_addr = ".".join(str(x) for x in (d_addr_list[::-1]))
        d_port = str(int(h_port, 16))
        return "{}:{}".format(d_addr, d_port)

    def mapper(self, sample):
        new_sample={}
        for k,entry in sample.items():
            
            h_tx_queue, h_rx_queue = entry['tx_queue:rx_queue'].split(":")

            new_sample[k] = {
                self.key : k,
                'time': entry['time'],
                'socket': "%s -> %s (inode:%s)" % ( self.convert_hex_socket(entry['local_address']),  self.convert_hex_socket(entry['rem_address']), entry['inode'] ) ,
                'tx_queue': int(h_tx_queue,16),
                'rx_queue': int(h_rx_queue,16),
                'drops': int(entry['drops']),
                'drops-per-sec': 0.0 ,
                 }

            if k in self.sample_old:
                new_sample[k]['drops-per-sec'] = 1.0*( new_sample[k]['drops'] - self.sample_old[k]['drops'] ) / ( new_sample[k]['time'] - self.sample_old[k]['time'] )
                if new_sample[k]['drops-per-sec'] < 0:
                    new_sample[k]['drops-per-sec']=0
                    
        return new_sample

    def add_diagrams(self, pdf, maxT):

        plt.clf()
        # Creating figure
        cm = 1/2.54                                         # centimeters in inches
        fig, axs = plt.subplots(3, dpi=72, figsize=(29.7*cm,21.0*cm))   # for landscape DIN A4

        fig.suptitle('%s' % self.file )

        #get current kernel parameter
        kernel_parameter={'/proc/sys/net/ipv4/udp_mem': "N/A",    
                '/proc/sys/net/ipv4/udp_rmem_min': "N/A",
                '/proc/sys/net/ipv4/udp_wmem_min': "N/A",
                '/proc/sys/net/core/rmem_default': "N/A",
                '/proc/sys/net/core/rmem_max': "N/A",
                '/proc/sys/net/core/wmem_default': "N/A",
                '/proc/sys/net/core/wmem_max': "N/A",
                }
        
        kernel_parameter_note=""
        for k,_ in kernel_parameter.items():
            result = self.proc_reader(k)
            if result:
                kernel_parameter[k] = ' '.join(result.split())
            
            kernel_parameter_note+= "%s: %s\n" % (k,kernel_parameter[k])
        
        axs[1].annotate(kernel_parameter_note, fontsize='xx-small', xy = (0, 0), xycoords='axes fraction')

        if not self.data_frame.empty:
            
            pivot_table=[]
            
            ######### Queue Size
            maxV=0
            for value in 'rx_queue tx_queue'.split():
                pivot_table = self.data_frame.pivot_table(index='time', columns=['socket'], values=value)
                pivot_table = pivot_table.loc[:, (pivot_table > 0).any()]
                
                maxV=max(maxV, pivot_table.max(axis=1).max(axis=0))
                
                for i in pivot_table.columns:
                    axs[0].plot( pivot_table[[i]].dropna(), label="%s , %s" % (i, value ) )
                
            if not pivot_table.columns.empty:
                axs[0].legend(fontsize='xx-small', loc= 'upper right')
                 
            axs[0].set_ylabel('Size of tx/rx Queues')
            axs[0].grid()
            axs[0].set_xlim(0,maxT)
            axs[0].set_ylim(0,maxV*1.05+0.01)

            ######### Drops
            maxV=0
            for value in ['drops']:
                pivot_table = self.data_frame.pivot_table(index='time', columns=['socket'], values=value)
                #pivot_table -= pivot_table.iloc[0].values.squeeze() # relative count wrt. start time
                pivot_table = pivot_table.loc[:, (pivot_table > 0).any()]
                
                maxV=max(maxV, pivot_table.max(axis=1).max(axis=0))
                
                for i in pivot_table.columns:
                    axs[1].plot( pivot_table[[i]].dropna(), label=i )
            
            if not pivot_table.columns.empty:
                axs[1].legend(fontsize='xx-small', loc= 'upper right')
            
            axs[1].set_ylabel('Packet Drops [count]')
            axs[1].grid()
            axs[1].set_xlim(0,maxT)
            axs[1].set_ylim(0,maxV*1.05+0.01)
            
            ######### Drop-Rate
            maxV=0
            for value in ['drops-per-sec']:
                pivot_table = self.data_frame.pivot_table(index='time', columns=['socket'], values=value)
                pivot_table = pivot_table.loc[:, (pivot_table > 0).any()]
                maxV=max(maxV, pivot_table.max(axis=1).max(axis=0))
                
                for i in pivot_table.columns:
                    axs[2].plot( pivot_table[[i]].dropna(), label=i )

            if not pivot_table.columns.empty:
                axs[2].legend(fontsize='xx-small', loc= 'upper right')

            axs[2].set_xlabel('Time t [s]')
            axs[2].set_ylabel('Packet Drop Rate [1/s]')
            axs[2].grid()
            axs[2].set_xlim(0,maxT)
            axs[2].set_ylim(0,maxV*1.05+0.01)

        pdf.savefig(fig)


class net_udp6(net_udp4):

    def __init__(self,config_yaml):
        super().__init__(config_yaml=config_yaml)
        self.file='/proc/net/udp6'

    def convert_hex_socket(self, hex_socket):
        h_addr, h_port = hex_socket.split(':')
        h_addr_list = ["".join(x) for x in zip(*[iter(str(h_addr))]*2)]
        h_addr_list = h_addr_list[:-4] + h_addr_list[:-5:-1] #reversed last 8 byte
        h_addr = ''.join(h_addr_list)
        h_addr_list = ["".join(x) for x in zip(*[iter(str(h_addr))]*4)]
        d_addr = ":".join(str(x).lower() for x in (h_addr_list))
        d_port = str(int(h_port, 16))
        return "{}:{}".format(d_addr, d_port)
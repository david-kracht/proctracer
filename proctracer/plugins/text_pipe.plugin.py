import os

from matplotlib import pyplot as plt

from plugin_proc_tracer_base import ProcTracerBase

BUFFER_SIZE = 65536

class text_pipe(ProcTracerBase):

    def __init__(self,config_yaml):
        super().__init__(
            config_yaml=config_yaml,
            file='',
            key='label',
            header_in='',
            )
        self.file = 'pipe @ %s' % self.config_yaml['pipe_path']
        self.fifo_fd = 0

        self.labels = {}
        self.counter = 0

    def start(self):
        try:
            os.mkfifo(self.config_yaml['pipe_path'])
        except Exception as e:
            os.unlink(self.config_yaml['pipe_path'])
            os.mkfifo(self.config_yaml['pipe_path'])

        self.fifo_fd = os.open(self.config_yaml['pipe_path'], os.O_RDONLY | os.O_NONBLOCK )

    def sample(self):
        sample={}
        bytes_string = os.read(self.fifo_fd, BUFFER_SIZE)

        if bytes_string:

            utf8_string = bytes_string.decode("utf-8")

            if utf8_string not in self.labels:
                self.labels[utf8_string] = self.counter
                self.counter += 1

            sample[self.key]={
                self.key: utf8_string,
                'time': self.t(),
                'level' : self.labels[utf8_string],
                }


        return sample

    def end(self):
        os.close(self.fifo_fd)
        os.unlink(self.config_yaml['pipe_path'])

    def add_diagrams(self, pdf, maxT):

        plt.clf()
        # Creating figure
        cm = 1/2.54                                         # centimeters in inches
        fig=plt.figure(dpi=72, figsize=(29.7*cm,21.0*cm))   # for landscape DIN A4

        fig.suptitle('%s' % self.file )

        if not self.data_frame.empty:

            pivot_table = self.data_frame.pivot_table(index='time', columns=[self.key], values='level')

            for i in pivot_table.columns:

                plt.plot( pivot_table[[i]].dropna(), label="%s" % (i),  marker = 'o')
                plt.title("Events")
                plt.xlabel("Time t [s]")
                plt.ylabel("Events")
                plt.yticks([])
                plt.legend(title="Event Labels", fontsize='small', loc= 'upper right')
                
                

        pdf.savefig(fig)


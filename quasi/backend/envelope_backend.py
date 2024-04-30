from photon_weave.state.envelope import Envelope

class EnvelopeBackend():

    def __init__(self):
        self.number_of_modes = 0

    def set_number_of_modes(self, number_of_modes):
        self.number_of_modes = number_of_modes

    def new_envelope(self):
        return Envelope()

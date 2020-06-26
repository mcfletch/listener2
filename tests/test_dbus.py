import unittest
from listener import models, defaults
from dbus.lowlevel import SignalMessage


class TestDBus(unittest.TestCase):
    def setUp(self):
        self.message = SignalMessage('/', defaults.DBUS_NAME, 'FinalMessage')

    def test_transcript_encode(self):
        pattern = models.Transcript.dbus_struct_signature()
        t = models.Transcript(
            words=['^', 'this'], confidence=-10, final=True, partial=False,
        )
        self.message.append(pattern, t.dbus_struct())

    def test_utterance_encode(self):

        pattern = models.Utterance.dbus_struct_signature()
        t = models.Transcript(
            words=['^', 'this'], confidence=-10, final=True, partial=False,
        )
        u = models.Utterance(
            transcripts=[t],
            messages=['a', 'b'],
            final=True,
            partial=False,
            utterance_number=4,
        )
        self.message.append(pattern, u.dbus_struct())

    def test_real_utterance_encode(self):
        self.message.append(
            '(iba(bdas))',
            (
                1593139040,
                True,
                [
                    (True, -14.70202922821045, ['testing']),
                    (True, -17.187391757965088, ['the', 'sting']),
                    (True, -17.871975898742676, ['thesting']),
                    (True, -18.0646390914917, ['theesting']),
                    (True, -18.168243408203125, ['teesting']),
                    (True, -18.567184448242188, ['thasting']),
                    (True, -18.66072368621826, ['thaesting']),
                    (True, -18.690112113952637, ['tasting']),
                    (True, -20.446099758148193, ['the', 'esting']),
                    (True, -20.985700607299805, ['t', 'esting']),
                    (True, -21.192089080810547, ['the', 'asting']),
                    (True, -21.913288116455078, ['te', 'esting']),
                    (True, -21.951452255249023, ['th', 'esting']),
                    (True, -22.788207054138184, ['ta', 'esting']),
                    (True, -23.690839767456055, ['tha', 'esting']),
                ],
            ),
        )
        self.message.append(
            '(iba(bdas))',
            (
                1593139920,
                True,
                [
                    (True, -10.453631401062012, ['h']),
                    (True, -10.928800582885742, ['e']),
                    (True, -11.342206478118896, ['n']),
                    (True, -12.607892513275146, ['he']),
                    (True, -13.158134460449219, ['d']),
                    (True, -13.176371097564697, ['u']),
                    (True, -13.342707633972168, ['a']),
                    (True, -14.17897891998291, ['m']),
                    (True, -14.235910892486572, ['hn']),
                    (True, -14.390232563018799, ['o']),
                    (True, -14.510844230651855, ['ne']),
                    (True, -15.418322563171387, ['hd']),
                    (True, -16.006152153015137, ['ho']),
                    (True, -17.820629596710205, ['hne']),
                ],
            ),
        )


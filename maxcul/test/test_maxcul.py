import unittest
from datetime import datetime

from maxcul._messages import MoritzMessage, SetTemperatureMessage, AckMessage, PairPingMessage, PairPongMessage, TimeInformationMessage, WallThermostatControlMessage, ThermostatStateMessage, MissingPayloadParameterError, WakeUpMessage

MESSAGE_SAMPLES = ["Z0C250442016F69039EA50028CC28",
                   "Z0E250202039EA5016F6900011904283C",
                   "Z0CBD0442016F69039EA50028CC35",
                   "Z0EBD0202039EA5016F69000119002841",
                   "Z0CC10442016F69039EA50028CA33",
                   "Z0EC10202039EA5016F69000119002835",
                   "Z0CC20442016F6903CEE20028CA36",
                   "Z0EC2020203CEE2016F6900011900281D",
                   "Z0CC30442016F69039EA50028CA35",
                   "Z0EC30202039EA5016F69000119002831",
                   "Z0B370630035BCC00CF400010EA",
                   "Z0B37000200CF40035BCC000035",
                   "Z0F00046016489C0000000019011E009732",
                   "Z0CC40442016F6903CEE20028C829",
                   "Z0EC4020203CEE2016F690001190028F9",
                   "Z0F00046016489C0000000019021E009631",
                   "Z0CC50442016F69039EA50028C829",
                   "Z0EC50202039EA5016F6900011900283E",
                   "Z0C250442016F69039EA50028CC28",
                   "Z0E250202039EA5016F6900011904283C",
                   "Z0F00046003CEE20000000019002800CC26",
                   "Z0C260442016F6903CEE20028CC26",
                   "Z0E26020203CEE2016F69000119002826",
                   "Z0F050460039EA50000000019002800CC2E",
                   "Z0C270442016F69039EA50028CC29",
                   "Z0E270202039EA5016F69000119002839",
                   "Z0C280442016F6903CEE20028CC2A",
                   "Z0E28020203CEE2016F69000119002828",
                   "Z0FFA050300CF40039EA500110A57E21534",
                   "Z0EFA0202039EA500CF40000119002839",
                   "Z0FE5050300CF40016F6900110A57E21535",
                   "Z0EE50202016F6900CF4000011904282B",
                   "Z0F7C050300CF4003CEE200110A57E21534",
                   "Z0E7C020203CEE200CF40000119002827",
                   "Z0FAE050300CF40012F4F00110A57E21535",
                   "Z0EAE0202012F4F00CF40000119001E0F",
                   "Z0F52050300CF4016489C00110A57E21534",
                   "Z0C290442016F69039EA50028CC2C",
                   "Z0E290202039EA5016F69000119002838",
                   "Z0C2A0442016F6903CEE20028CC2A",
                   "Z0E2A020203CEE2016F69000119002824",
                   "Z0C2B0442016F69039EA50028CC2A",
                   "Z0E2B0202039EA5016F69000119002836",
                   "Z0C2C0442016F6903CEE20028CA29",
                   "Z0E2C020203CEE2016F69000119002821",
                   "Z0B370630035BCC00CF40001019",
                   "Z0B37000200CF40035BCC000034",
                   "Z0C2D0442016F69039EA50028CA29",
                   "Z0E2D0202039EA5016F69000119002836",
                   "Z0C2E0442016F6903CEE20028CA2A",
                   "Z0E2E020203CEE2016F69000119002822",
                   "Z0B7406300360C600CF40001040",
                   "Z0B74000200CF400360C6000031",
                   "Z0C2F0442016F69039EA50028C82D",
                   "Z0E2F0202039EA5016F69000119002831",
                   "Z0C300442016F6903CEE20028C82C",
                   "Z0E30020203CEE2016F69000119002821",
                   "Z0F00046003CEE20000000019042800C821",
                   "Z0F050460039EA50000000019042800C830",
                   "Z0C310442016F69039EA50028C82C",
                   "Z0E310202039EA5016F69000119042830",
                   "Z0C320442016F6903CEE20028C82D",
                   "Z0E32020203CEE2016F69000119042820",
                   "Z0F00046016489C0000000019011E009724",
                   "Z0C330442016F69039EA50028C72C",
                   "Z0E330202039EA5016F69000119042830",
                   "Z0F00046016489C0000000019021E009623",
                   "Z0B0C0630163DF000CF4000100D",
                   "Z0B0C000200CF40163DF0000037",
                   "Z0F00046016489C0000000019031E009622",
                   "Z0C340442016F6903CEE20028C72C",
                   "Z0E34020203CEE2016F69000119042820",
                   "Z0F00046016489C0000000019051E009623",
                   "Z0C350442016F69039EA50028C72C",
                   "Z0E350202039EA5016F69000119042830",
                   "Z0C360442016F6903CEE20028C82C",
                   "Z0E36020203CEE2016F69000119042820",
                   "Z0F00046016489C0000000019041E009A23",
                   "Z0C370442016F69039EA50028C82C",
                   "Z0E370202039EA5016F69000119042830",
                   "Z0F00046016489C0000000019001E009A23",
                   "Z0C380442016F6903CEE20028C82D",
                   "Z0E38020203CEE2016F69000119042821",
                   "Z0C390442016F69039EA50028CA2D",
                   "Z0E390202039EA5016F69000119042832",
                   "Z0C3A0442016F6903CEE20028CA2C",
                   "Z0E3A020203CEE2016F69000119042822",
                   "Z0C3B0442016F69039EA50028CA2C",
                   "Z0E3B0202039EA5016F69000119042833",
                   "Z0C3C0442016F6903CEE20028CA2C",
                   "Z0E3C020203CEE2016F69000119042821",
                   "Z0C3D0442016F69039EA50028CA2C",
                   "Z0E3D0202039EA5016F69000119042832",
                   "Z0C3E0442016F6903CEE20028CA2D",
                   "Z0E3E020203CEE2016F69000119042820",
                   "Z0C3F0442016F69039EA50028CA2D",
                   "Z0E3F0202039EA5016F69000119042833",
                   "Z0C400442016F6903CEE20028CA2C",
                   "Z0E40020203CEE2016F69000119042822",
                   "Z0C410442016F69039EA50028CA2A",
                   "Z0E410202039EA5016F69000119042832",
                   "Z0B370630035BCC00CF4000101A",
                   "Z0B37000200CF40035BCC000036",
                   "Z0C420442016F6903CEE20028CA2A",
                   "Z0E42020203CEE2016F69000119042820",
                   "Z0C430442016F69039EA50028CA2A",
                   "Z0E430202039EA5016F69000119042831",
                   "Z0B7406300360C600CF40001037",
                   "Z0B74000200CF400360C6000037",
                   "Z0C440442016F6903CEE20028CA2A",
                   "Z0E44020203CEE2016F6900011904281F",
                   "Z0C450442016F69039EA50028CA29",
                   "Z0E450202039EA5016F6900011904282F",
                   "Z0C460442016F6903CEE20028CA29",
                   "Z0E46020203CEE2016F6900011904281F",
                   "Z0C470442016F69039EA50028CA29",
                   "Z0E470202039EA5016F6900011904282F",
                   "Z0C480442016F6903CEE20028CA29",
                   "Z0E48020203CEE2016F6900011904281F",
                   "Z0F00046016489C0000000019011E009722",
                   "Z0B0C0630163DF000CF4000100C",
                   "Z0B0C000200CF40163DF0000037",
                   "Z0F00046016489C0000000019021E009622",
                   "Z0C490442016F69039EA50028CC29",
                   "Z0E490202039EA5016F6900011904282F",
                   "Z0F00046016489C0000000019051E009522",
                   "Z0C4A0442016F6903CEE20028CC29",
                   "Z0E4A020203CEE2016F6900011904281E",
                   "Z0F00046016489C0000000019061E009622",
                   "Z0C4B0442016F69039EA50028CC29",
                   "Z0E4B0202039EA5016F6900011904282F",
                   "Z0C4C0442016F6903CEE20028CC29",
                   "Z0E4C020203CEE2016F6900011904281F",
                   "Z0C4D0442016F69039EA50028CC2B",
                   "Z0E4D0202039EA5016F69000119042835",
                   "Z0F00046016489C0000000019021E009A21",
                   "Z0F00046003CEE20000000019002800CC23",
                   "Z0F050460039EA50000000019002800CC35",
                   "Z0C4E0442016F6903CEE20028CC2A",
                   "Z0E4E020203CEE2016F69000119002823",
                   "Z0F00046016489C0000000019011E009A20",
                   "Z0F00046016489C0000000019001E009D21",
                   "Z0C4F0442016F69039EA50028CE2B",
                   "Z0E4F0202039EA5016F69000119002835",
                   "Z0C500442016F6903CEE20028CC2B",
                   "Z0E50020203CEE2016F69000119002823",
                   "Z0C510442016F69039EA50028CC2A",
                   "Z0E510202039EA5016F69000119002835",
                   "Z0C520442016F6903CEE20028CC2A",
                   "Z0E52020203CEE2016F69000119002824",
                   "Z0C530442016F69039EA50028CC2B",
                   "Z0E530202039EA5016F69000119002835",
                   "Z0C540442016F6903CEE20028CC2B",
                   "Z0E54020203CEE2016F69000119002824",
                   "Z0C550442016F69039EA50028CC2B",
                   "Z0E550202039EA5016F69000119002836",
                   "Z0C560442016F6903CEE20028CA29",
                   "Z0E56020203CEE2016F6900011900281C",
                   "Z0B370630035BCC00CF40001019",
                   "Z0B37000200CF40035BCC000037",
                   "Z0C570442016F69039EA50028CA2A",
                   "Z0E570202039EA5016F6900011900282C",
                   "Z0C580442016F6903CEE20028CA2A",
                   "Z0E58020203CEE2016F6900011900281C",
                   "Z0B7406300360C600CF40001037",
                   "Z0B74000200CF400360C6000038",
                   "Z0C590442016F69039EA50028C82C",
                   "Z0E590202039EA5016F69000119002834",
                   "Z0C5A0442016F6903CEE20028C82C",
                   "Z0E5A020203CEE2016F69000119002823",
                   "Z0F050460039EA50000000019042800C834",
                   "Z0C5B0442016F69039EA50028C82C",
                   "Z0E5B0202039EA5016F69000119042834",
                   "Z0F00046003CEE20000000019042800C823",
                   "Z0C5C0442016F6903CEE20028C72C",
                   "Z0E5C020203CEE2016F69000119042823",
                   "Z0B0C0630163DF000CF40001007",
                   "Z0B0C000200CF40163DF0000038",
                   "Z0C5D0442016F69039EA50028C72C",
                   "Z0E5D0202039EA5016F69000119042834",
                   "Z0C5E0442016F6903CEE20028C72C",
                   "Z0E5E020203CEE2016F69000119042822",
                   "Z0C5F0442016F69039EA50028C72C",
                   "Z0E5F0202039EA5016F69000119042834",
                   "Z0C600442016F6903CEE20028C72C",
                   "Z0E60020203CEE2016F69000119042824",
                   "Z0F00046016489C0000000019011E00971C",
                   "Z0F00046016489C0000000019021E009616",
                   "Z0C610442016F69039EA50028C725",
                   "Z0E610202039EA5016F6900011904282A",
                   "Z0F00046016489C0000000019031E009614",
                   "Z0C620442016F6903CEE20028C724",
                   "Z0E62020203CEE2016F6900011904281E",
                   "Z0F00046016489C0000000019051E009614",
                   "Z0C630442016F69039EA50028C824",
                   "Z0E630202039EA5016F6900011904282B",
                   "Z0C640442016F6903CEE20028C825",
                   "Z0E64020203CEE2016F6900011904281D",
                   "Z0C650442016F69039EA50028C825",
                   "Z0E650202039EA5016F6900011904282B",
                   "Z0F00046016489C0000000019031E009A14",
                   "Z0C660442016F6903CEE20028CA25",
                   "Z0E66020203CEE2016F6900011904281E",
                   "Z0F00046016489C0000000019011E009A15",
                   "Z0F00046016489C0000000019001E009B14",
                   "Z0C670442016F69039EA50028CA24",
                   "Z0E670202039EA5016F6900011904282B",
                   "Z0C680442016F6903CEE20028CA25",
                   "Z0E68020203CEE2016F6900011904281E",
                   "Z0C690442016F69039EA50028CA24",
                   "Z0E690202039EA5016F6900011904282B",
                   "Z0C6A0442016F6903CEE20028CA24",
                   "Z0E6A020203CEE2016F6900011904281F",
                   "Z0C6B0442016F69039EA50028CA24",
                   "Z0E6B0202039EA5016F6900011904282B",
                   "Z0B370630035BCC00CF40001018",
                   "Z0B37000200CF40035BCC000033",
                   "Z0C6C0442016F6903CEE20028CA25",
                   "Z0E6C020203CEE2016F6900011904281D",
                   "Z0C6D0442016F69039EA50028CA25",
                   "Z0E6D0202039EA5016F6900011904282B",
                   "Z0B7406300360C600CF40001037",
                   "Z0B74000200CF400360C6000033",
                   "Z0C6E0442016F6903CEE20028CA25",
                   "Z0E6E020203CEE2016F6900011904281E",
                   "Z0C6F0442016F69039EA50028CA24",
                   "Z0E6F0202039EA5016F6900011904282B",
                   "Z0C700442016F6903CEE20028CA2B",
                   "Z0E70020203CEE2016F69000119042822",
                   "Z0C710442016F69039EA50028CA2B",
                   "Z0E710202039EA5016F69000119042818",
                   "Z0B0C0630163DF000CF40001005",
                   "Z0B0C000200CF40163DF0000039",
                   "Z0C720442016F6903CEE20028CA2B",
                   "Z0E72020203CEE2016F69000119042821",
                   "Z0C730442016F69039EA50028CA2B",
                   "Z0E730202039EA5016F69000119042814",
                   "Z0C740442016F6903CEE20028CA2B",
                   "Z0E74020203CEE2016F69000119042821",
                   "Z0C750442016F69039EA50028CA2B",
                   "Z0E750202039EA5016F69000119042818",
                   "Z0C760442016F6903CEE20028CA2B",
                   "Z0E76020203CEE2016F69000119042821",
                   "Z0F00046016489C0000000019011E009616",
                   "Z0C770442016F69039EA50028CA2B",
                   "Z0E770202039EA5016F69000119042813",
                   "Z0F00046016489C0000000019031E009614",
                   "Z0C780442016F6903CEE20028CA2B",
                   "Z0E78020203CEE2016F69000119042821",
                   "Z0F00046016489C0000000019041E009615",
                   "Z0F00046016489C0000000019051E009615",
                   "Z0C790442016F69039EA50028CA2B",
                   "Z0E790202039EA5016F69000119042815",
                   "Z0C7A0442016F6903CEE20028CA2B",
                   "Z0E7A020203CEE2016F69000119042821",
                   "Z0C7B0442016F69039EA50028CA2A",
                   "Z0E7B0202039EA5016F690001190428F2",
                   "Z0C7C0442016F6903CEE20028CA2A",
                   "Z0E7C020203CEE2016F69000119042821",
                   "Z0F00046016489C0000000019031E009A18",
                   "Z0C7D0442016F69039EA50028CC2B",
                   "Z0E7D0202039EA5016F690001190428F8",
                   "Z0F00046016489C0000000019011E009A1F",
                   "Z0C7E0442016F6903CEE20028CC2A",
                   "Z0E7E020203CEE2016F69000119042820",
                   "Z0F00046016489C0000000019001E009B19",
                   "Z0C7F0442016F69039EA50028CC2B",
                   "Z0E7F0202039EA5016F69000119042835",
                   "Z0C800442016F6903CEE20028CC2A",
                   "Z0E80020203CEE2016F69000119042821",
                   "Z0B370630035BCC00CF4000101C",
                   "Z0B37000200CF40035BCC000034",
                   "Z0C810442016F69039EA50028CC2B",
                   "Z0E810202039EA5016F69000119042835",
                   "Z0C820442016F6903CEE20028CC2B",
                   "Z0E82020203CEE2016F69000119002821",
                   "Z0F00046003CEE20000000019002800CC20",
                   "Z0F050460039EA50000000019002800CC35",
                   "Z0B7406300360C600CF40001038",
                   "Z0B74000200CF400360C6000034",
                   "Z0C830442016F69039EA50028CC2A",
                   "Z0E830202039EA5016F69000119002835",
                   "Z0C840442016F6903CEE20028CC2A",
                   "Z0E84020203CEE2016F69000119002821",
                   "Z0C850442016F69039EA50028CC2A",
                   "Z0E850202039EA5016F69000119002835",
                   "Z0B0C0630163DF000CF40001008",
                   "Z0B0C000200CF40163DF0000034",
                   "Z0C860442016F6903CEE20028CC2A",
                   "Z0E86020203CEE2016F69000119002820",
                   "Z0C870442016F69039EA50028CC2A",
                   "Z0E870202039EA5016F69000119002835",
                   "Z0C880442016F6903CEE20028CA2A",
                   "Z0E88020203CEE2016F69000119002820",
                   "Z0C890442016F69039EA50028CA2B",
                   "Z0E890202039EA5016F69000119002834",
                   "Z0C8A0442016F6903CEE20028CA2F",
                   "Z0E8A020203CEE2016F69000119002828",
                   "Z0CA0025000077712345600100121",
                   "Z0CA002500007771234560050011E",
                   "Z0CA002500007771234560050011E",
                   "Z0CA102500007771234560010001E",
                   "Z0CA102500007771234560050001E",
                   "Z0CA102500007771234560050001F",
                   "Z0CA1025000077712345600500020",
                   "Z0B010030019977000000000041",
                   "Z0B01003001997700000000021C",
                   "Z0B020030019977000000000036"]

class MessageSampleInputListTestCase(unittest.TestCase):
    def test_list_input(self):
        for sample in MESSAGE_SAMPLES:
            with self.subTest("Decode " + sample):
                MoritzMessage.decode_message(sample)

    def test_unknown_messages(self):
        sample = "Z0E250210039EA5016F6900011904283C"
        with self.assertRaises(NotImplementedError):
            MoritzMessage.decode_message(sample)

class MessageSampleInputTestCase(unittest.TestCase):
    def test_thermostat_state(self):
        sample = "Z0F61046008FFE90000000019002000CA"
        msg = MoritzMessage.decode_message(sample)
        self.assertTrue(isinstance(msg, ThermostatStateMessage))
        self.assertEqual(msg.counter, 0x61)
        self.assertEqual(msg.flag, 0x4)
        self.assertEqual(msg.sender_id, 0x8FFE9)
        self.assertEqual(msg.receiver_id, 0x0)
        self.assertEqual(msg.group_id, 0)
        self.assertEqual(msg.decode_payload('19002000CA'), {
            'battery_low': False,
            'desired_temperature': 16.0,
            'dstsetting': False,
            'is_locked': False,
            'langateway': True,
            'measured_temperature': 20.2,
            'mode': 'manual',
            'rferror': False,
            'valve_position': 0
        })

    def test_set_temperature(self):
        sample = "Z0BB900401234560B3554004B"
        msg = MoritzMessage.decode_message(sample)
        self.assertTrue(isinstance(msg, SetTemperatureMessage))
        self.assertEqual(msg.counter, 0xB9)
        self.assertEqual(msg.flag, 0x0)
        self.assertEqual(msg.sender_id, 0x123456)
        self.assertEqual(msg.receiver_id, 0x0B3554)
        self.assertEqual(msg.group_id, 0)
        self.assertEqual(msg.decode_payload('4B'), {
            'desired_temperature': 5.5,
            'mode': 'manual',
        })

    def test_set_temp_ack(self):
        sample = "Z0EB902020B3554123456000119000B"
        msg = MoritzMessage.decode_message(sample)
        self.assertTrue(isinstance(msg, AckMessage))
        self.assertEqual(msg.counter, 0xB9)
        self.assertEqual(msg.sender_id, 0x0B3554)
        self.assertEqual(msg.receiver_id, 0x123456)
        self.assertEqual(msg.group_id, 0)
        self.assertEqual(msg.decode_payload('0119000B'), {
            'battery_low': False,
            'desired_temperature': 5.5,
            'dstsetting': False,
            'is_locked': False,
            'langateway': True,
            'mode': 'manual',
            'rferror': False,
            'state': 'ok',
            'valve_position': 0,
        })

    def test_pair_ping(self):
        sample = "Z170004000E016C000000001001A04B455130393932343736"
        msg = MoritzMessage.decode_message(sample)
        self.assertTrue(isinstance(msg, PairPingMessage))
        self.assertEqual(msg.counter, 0x0)
        self.assertEqual(msg.flag, 0x04)
        self.assertEqual(msg.sender_id, 0xE016C)
        self.assertEqual(msg.receiver_id, 0x0)
        self.assertEqual(msg.group_id, 0)
        self.assertEqual(msg.decode_payload('1001A04B455130393932343736'), {
            'firmware_version': "V1.0",
            'device_type': "HeatingThermostat",
            'selftest_result': 0xA0,
            'device_serial': "KEQ0992476",
        })

    def test_pair_pong(self):
        sample = "Z0B0100011234560E016C0000"
        msg = MoritzMessage.decode_message(sample)
        self.assertTrue(isinstance(msg, PairPongMessage))
        self.assertEqual(msg.counter, 0x1)
        self.assertEqual(msg.flag, 0x00)
        self.assertEqual(msg.sender_id, 0x123456)
        self.assertEqual(msg.receiver_id, 0xE016C)
        self.assertEqual(msg.group_id, 0)
        self.assertEqual(msg.decode_payload('00'), {
            'device_type': "Cube",
        })

    def test_time_information_question(self):
        sample = "Z0A000A030E016C12345600"
        msg = MoritzMessage.decode_message(sample)
        self.assertTrue(isinstance(msg, TimeInformationMessage))
        self.assertEqual(msg.counter, 0x00)
        self.assertEqual(msg.flag, 0x0A)
        self.assertEqual(msg.sender_id, 0xE016C)
        self.assertEqual(msg.receiver_id, 0x123456)
        self.assertEqual(msg.group_id, 0)

    def test_time_information(self):
        sample = "Z0F0204031234560E016C000E0102E117"
        msg = MoritzMessage.decode_message(sample)
        self.assertTrue(isinstance(msg, TimeInformationMessage))
        self.assertEqual(msg.counter, 0x02)
        self.assertEqual(msg.flag, 0x04)
        self.assertEqual(msg.sender_id, 0x123456)
        self.assertEqual(msg.receiver_id, 0xE016C)
        self.assertEqual(msg.group_id, 0)
        self.assertEqual(msg.decode_payload("0E0102E117"), {'datetime': datetime(2014, 12, 1, 2, 33, 23)})

    def test_wallthermostat_control_message(self):
        sample = "Z0CB9044217A95512DC400019D9"
        msg = MoritzMessage.decode_message(sample)
        self.assertTrue(isinstance(msg, WallThermostatControlMessage))
        self.assertEqual(msg.counter, 0xB9)
        self.assertEqual(msg.flag, 0x04)
        self.assertEqual(msg.sender_id, 0x17A955)
        self.assertEqual(msg.receiver_id, 0x12DC40)
        self.assertEqual(msg.group_id, 0)
        self.assertEqual(msg.decode_payload("19D9"), {
            "desired_temperature": 12.5,
            "temperature": 21.7
        })
        #wallthermostat updated <WallThermostatStateMessage counter:c0 flag:4 sender:17a955 receiver:0 group:0 payload:59011900D9>


class MessageGeneralOutputTestCase(unittest.TestCase):
    def test_encoding_without_payload(self):
        expected_result = "Zs0AB900F11234560B355400"
        msg = WakeUpMessage()
        msg.counter = 0xB9
        msg.sender_id = 0x123456
        msg.receiver_id = 0x0B3554
        msg.group_id = 0
        encoded_message = msg.encode_message()
        self.assertEqual(encoded_message, expected_result)

    def test_encoding_with_payload(self):
        expected_result = "Zs0BB900401234560B3554004B"
        msg = SetTemperatureMessage()
        msg.counter = 0xB9
        msg.sender_id = 0x123456
        msg.receiver_id = 0x0B3554
        msg.group_id = 0
        msg.desired_temperature = 5.5
        msg.mode = 'manual'
        encoded_message = msg.encode_message()
        self.assertEqual(encoded_message, expected_result)
        self.assertEqual(msg.encode_payload(), expected_result[-2:])

    def test_encoding_with_broken_payload(self):
        msg = SetTemperatureMessage()
        msg.counter = 0xB9
        msg.sender_id = 0x123456
        msg.receiver_id = 0x0B3554
        msg.group_id = 0
        msg.mode = 'manual'
        with self.assertRaises(MissingPayloadParameterError):
            msg.encode_message()


class MessageOutputSampleTestCase(unittest.TestCase):
    def test_set_temperature(self):
        msg = SetTemperatureMessage()
        msg.counter = 0xB9
        msg.sender_id = 0x123456
        msg.receiver_id = 0x0B3554
        msg.group_id = 0
        msg.desired_temperature = 5.5
        msg.mode = 'manual'
        self.assertEqual(msg.encode_message(), "Zs0BB900401234560B3554004B")

    def test_set_timeinformation(self):
        msg = TimeInformationMessage()
        msg.counter = 0x02
        msg.sender_id = 0x123456
        msg.receiver_id = 0xE016C
        msg.group_id = 0x0
        msg.datetime = datetime(2014, 12, 1, 2, 33, 23)
        self.assertEqual(msg.encode_message(), "Zs0F0204031234560E016C000E0102E117")

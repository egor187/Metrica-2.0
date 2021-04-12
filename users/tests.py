from django.test import TestCase, Client

from users.models import CustomUser, Claim, ClaimTopic


class FeedbackTest(TestCase):
    def setUp(self):
        self.client = Client()
        test_user = CustomUser.objects.create(username='tester')
        test_user.set_password('test_password')
        self.client.login(username='tester', password='test_password')

    def test_feedback(self):
        user = CustomUser.objects.get(username='tester')
        self.assertEqual(CustomUser.objects.get(), user)

        topic = ClaimTopic.objects.create(name='first_topic')
        self.assertEqual(ClaimTopic.objects.get(), topic)

        claim = Claim.objects.create(topic=topic, claim='test_claim', claimer=user)
        self.assertEqual(Claim.objects.get(), claim)

from django.test import TestCase, Client
from django.urls import reverse_lazy

from games.models import Games


class GamesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.game = Games.objects.create(name='Test game')

    def test_index_view(self):
        response = self.client.get(reverse_lazy('games:games_index'))
        self.assertIs(response.status_code, 200)
        self.assertTrue(response.context['games'])
        self.assertContains(response, self.game)
        self.assertEqual(response.context['games'][0], self.game)
        self.assertIn('games', response.context)
        self.assertTemplateUsed(response, 'games_index.html')

    def test_detail_view(self):
        new_game = Games.objects.create(name='Test game 2')
        response = self.client.get(reverse_lazy('games:games_detail', args=[2, ]))
        self.assertEqual(response.context['game'].name, new_game.name)

    def test_add_game(self):
        response = self.client.get(reverse_lazy('games:games_index'))
        Games.objects.create(name='Test game 2')
        self.assertQuerysetEqual(
            response.context['games'].order_by('name'),
            ['<Games: Test game>', '<Games: Test game 2>']
        )

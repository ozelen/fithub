from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .factories import BodyMeasurementFactory, GoalFactory, UserFactory
from .models import BodyMeasurement, Goal


class GoalsAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_goal_list_authenticated(self):
        """Test that authenticated users can list their goals"""
        goal1 = GoalFactory(user=self.user)
        goal2 = GoalFactory(user=self.user)
        goal3 = GoalFactory(user=self.other_user)  # Should not appear

        url = reverse("goal-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        goal_ids = [goal["id"] for goal in response.data["results"]]
        self.assertIn(str(goal1.id), goal_ids)
        self.assertIn(str(goal2.id), goal_ids)
        self.assertNotIn(str(goal3.id), goal_ids)

    def test_goal_create(self):
        """Test creating a new goal"""
        url = reverse("goal-list")
        data = {
            "goal_type": "weight_loss",
            "target_date": (date.today() + timedelta(days=30)).isoformat(),
            "notes": "Test goal notes",
            "is_active": True,
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Goal.objects.count(), 1)
        goal = Goal.objects.first()
        self.assertEqual(goal.user, self.user)
        self.assertEqual(goal.goal_type, "weight_loss")

    def test_goal_activate(self):
        """Test activating a goal"""
        goal1 = GoalFactory(user=self.user, is_active=False)
        goal2 = GoalFactory(user=self.user, is_active=True)

        url = reverse("goal-activate", kwargs={"pk": goal1.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal1.refresh_from_db()
        goal2.refresh_from_db()
        self.assertTrue(goal1.is_active)
        self.assertFalse(goal2.is_active)

    def test_goal_deactivate(self):
        """Test deactivating a goal"""
        goal = GoalFactory(user=self.user, is_active=True)

        url = reverse("goal-deactivate", kwargs={"pk": goal.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertFalse(goal.is_active)

    def test_goal_active_endpoint(self):
        """Test getting all active goals"""
        active_goal1 = GoalFactory(user=self.user, is_active=True)
        active_goal2 = GoalFactory(user=self.user, is_active=True)
        inactive_goal = GoalFactory(user=self.user, is_active=False)

        url = reverse("goal-active")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        goal_ids = [goal["id"] for goal in response.data]
        self.assertIn(str(active_goal1.id), goal_ids)
        self.assertIn(str(active_goal2.id), goal_ids)
        self.assertNotIn(str(inactive_goal.id), goal_ids)

    def test_goal_by_type(self):
        """Test getting goals by type"""
        weight_loss_goal = GoalFactory(user=self.user, goal_type="weight_loss")
        muscle_gain_goal = GoalFactory(user=self.user, goal_type="muscle_gain")

        url = reverse("goal-by-type")
        response = self.client.get(url, {"type": "weight_loss"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(weight_loss_goal.id))

    def test_goal_upcoming(self):
        """Test getting upcoming goals"""
        future_goal = GoalFactory(
            user=self.user,
            target_date=date.today() + timedelta(days=30),
            is_active=True,
        )
        past_goal = GoalFactory(
            user=self.user,
            target_date=date.today() - timedelta(days=30),
            is_active=True,
        )

        url = reverse("goal-upcoming")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(future_goal.id))

    def test_goal_overdue(self):
        """Test getting overdue goals"""
        overdue_goal = GoalFactory(
            user=self.user,
            target_date=date.today() - timedelta(days=30),
            is_active=True,
        )
        future_goal = GoalFactory(
            user=self.user,
            target_date=date.today() + timedelta(days=30),
            is_active=True,
        )

        url = reverse("goal-overdue")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(overdue_goal.id))

    def test_goal_progress(self):
        """Test getting goal progress"""
        goal = GoalFactory(user=self.user)

        # Create some measurements
        measurement1 = BodyMeasurementFactory(
            user=self.user,
            metric="weight_kg",
            value=80.0,
            timestamp=timezone.now() - timedelta(days=30),
        )
        measurement2 = BodyMeasurementFactory(user=self.user, metric="weight_kg", value=75.0, timestamp=timezone.now())

        url = reverse("goal-progress", kwargs={"pk": goal.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("goal", response.data)
        self.assertIn("latest_measurement", response.data)
        self.assertIn("first_measurement", response.data)
        self.assertEqual(response.data["measurements_count"], 2)

    def test_body_measurement_list_authenticated(self):
        """Test that authenticated users can list their measurements"""
        measurement1 = BodyMeasurementFactory(user=self.user)
        measurement2 = BodyMeasurementFactory(user=self.user)
        measurement3 = BodyMeasurementFactory(user=self.other_user)  # Should not appear

        url = reverse("bodymeasurement-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        measurement_ids = [m["id"] for m in response.data["results"]]
        self.assertIn(measurement1.id, measurement_ids)
        self.assertIn(measurement2.id, measurement_ids)
        self.assertNotIn(measurement3.id, measurement_ids)

    def test_body_measurement_create(self):
        """Test creating a new body measurement"""
        url = reverse("bodymeasurement-list")
        data = {
            "metric": "weight_kg",
            "measurement_type": "log",
            "value": 75.5,
            "timestamp": timezone.now().isoformat(),
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BodyMeasurement.objects.count(), 1)
        measurement = BodyMeasurement.objects.first()
        self.assertEqual(measurement.user, self.user)
        self.assertEqual(measurement.metric, "weight_kg")

    def test_body_measurement_latest(self):
        """Test getting latest measurements for each metric"""
        # Create measurements for different metrics
        weight_measurement = BodyMeasurementFactory(
            user=self.user,
            metric="weight_kg",
            value=75.0,
            timestamp=timezone.now() - timedelta(days=1),
        )
        weight_measurement_latest = BodyMeasurementFactory(
            user=self.user, metric="weight_kg", value=74.5, timestamp=timezone.now()
        )
        body_fat_measurement = BodyMeasurementFactory(user=self.user, metric="body_fat_percentage", value=15.0)

        url = reverse("bodymeasurement-latest")
        response = self.client.get(url, {"metrics": ["weight_kg", "body_fat_percentage"]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Check that we get the latest weight measurement
        weight_data = next(m for m in response.data if m["metric"] == "weight_kg")
        self.assertEqual(weight_data["value"], 74.5)

    def test_body_measurement_by_metric(self):
        """Test getting measurements by specific metric"""
        weight_measurement1 = BodyMeasurementFactory(user=self.user, metric="weight_kg", value=75.0)
        weight_measurement2 = BodyMeasurementFactory(user=self.user, metric="weight_kg", value=74.5)
        body_fat_measurement = BodyMeasurementFactory(user=self.user, metric="body_fat_percentage", value=15.0)

        url = reverse("bodymeasurement-by-metric")
        response = self.client.get(url, {"metric": "weight_kg"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        metric_values = [m["metric"] for m in response.data]
        self.assertTrue(all(m == "weight_kg" for m in metric_values))

    def test_body_measurement_trends(self):
        """Test getting measurement trends over time"""
        # Create measurements for the last 30 days
        for i in range(30):
            BodyMeasurementFactory(
                user=self.user,
                metric="weight_kg",
                value=75.0 - (i * 0.1),  # Gradual weight loss
                timestamp=timezone.now() - timedelta(days=i),
            )

        url = reverse("bodymeasurement-trends")
        response = self.client.get(url, {"metric": "weight_kg", "days": 30})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["metric"], "weight_kg")
        self.assertEqual(response.data["period_days"], 30)
        self.assertEqual(len(response.data["measurements"]), 30)
        self.assertEqual(response.data["count"], 30)

    def test_body_measurement_summary(self):
        """Test getting measurement summary for all metrics"""
        weight_measurement = BodyMeasurementFactory(user=self.user, metric="weight_kg", value=75.0)
        body_fat_measurement = BodyMeasurementFactory(user=self.user, metric="body_fat_percentage", value=15.0)

        url = reverse("bodymeasurement-summary")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("weight_kg", response.data)
        self.assertIn("body_fat_percentage", response.data)
        self.assertEqual(response.data["weight_kg"]["latest_value"], 75.0)
        self.assertEqual(response.data["body_fat_percentage"]["latest_value"], 15.0)

    def test_body_measurement_bulk_create(self):
        """Test creating multiple measurements at once"""
        url = reverse("bodymeasurement-bulk-create")
        data = {
            "measurements": [
                {
                    "metric": "weight_kg",
                    "measurement_type": "log",
                    "value": 75.0,
                    "timestamp": timezone.now().isoformat(),
                },
                {
                    "metric": "body_fat_percentage",
                    "measurement_type": "log",
                    "value": 15.0,
                    "timestamp": timezone.now().isoformat(),
                },
            ]
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BodyMeasurement.objects.count(), 2)
        self.assertEqual(len(response.data), 2)

    def test_unauthorized_access(self):
        """Test that unauthenticated users cannot access endpoints"""
        self.client.force_authenticate(user=None)

        url = reverse("goal-list")
        response = self.client.get(url)

        # JWT authentication returns 401, Token authentication returns 403
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_cross_user_access_denied(self):
        """Test that users cannot access other users' data"""
        other_goal = GoalFactory(user=self.other_user)

        url = reverse("goal-detail", kwargs={"pk": other_goal.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pagination(self):
        """Test that pagination works correctly"""
        # Create 25 goals to test pagination (default page size is 20)
        for _ in range(25):
            GoalFactory(user=self.user)

        url = reverse("goal-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 20)  # First page
        self.assertIsNotNone(response.data["next"])  # Has next page

    def test_filtering(self):
        """Test filtering functionality"""
        active_goal = GoalFactory(user=self.user, is_active=True)
        inactive_goal = GoalFactory(user=self.user, is_active=False)

        url = reverse("goal-list")
        response = self.client.get(url, {"is_active": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], str(active_goal.id))

    def test_search(self):
        """Test search functionality"""
        goal1 = GoalFactory(user=self.user, notes="Weight loss journey")
        goal2 = GoalFactory(user=self.user, notes="Muscle building program")

        url = reverse("goal-list")
        response = self.client.get(url, {"search": "weight"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], str(goal1.id))

    def test_ordering(self):
        """Test ordering functionality"""
        goal1 = GoalFactory(user=self.user, target_date=date.today() + timedelta(days=30))
        goal2 = GoalFactory(user=self.user, target_date=date.today() + timedelta(days=10))

        url = reverse("goal-list")
        response = self.client.get(url, {"ordering": "target_date"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["target_date"], goal2.target_date.isoformat())
        self.assertEqual(response.data["results"][1]["target_date"], goal1.target_date.isoformat())

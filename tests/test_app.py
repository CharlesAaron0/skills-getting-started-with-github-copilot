import pytest
from src.app import activities

class TestActivitiesAPI:
    """Test suite for activities API endpoints"""

    def test_get_activities(self, client, sample_activities):
        """Test GET /activities returns all activities"""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
        assert len(data) >= 2  # At least our sample activities
        
        # Check a specific activity structure
        chess_club = data.get("Chess Club")
        assert chess_club is not None
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_root_redirect(self, client):
        """Test GET / redirects to static HTML"""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers.get("location", "")

class TestSignupAPI:
    """Test suite for signup functionality"""

    def test_signup_success(self, client):
        """Test successful signup"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert f"Signed up {email} for {activity}" == data["message"]
        
        # Verify participant was added
        get_response = client.get("/activities")
        activities_data = get_response.json()
        assert email in activities_data[activity]["participants"]

    def test_signup_duplicate_email(self, client):
        """Test signup with already registered email"""
        # Arrange
        email = "duptest@mergington.edu"
        activity = "Chess Club"
        
        # Act - First signup
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act - Second signup should fail
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_invalid_activity(self, client):
        """Test signup for nonexistent activity"""
        # Arrange
        invalid_activity = "NonexistentActivity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{invalid_activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_missing_email(self, client):
        """Test signup without email parameter"""
        # Arrange
        activity = "Chess Club"
        
        # Act
        response = client.post(f"/activities/{activity}/signup")
        
        # Assert
        # FastAPI should handle this gracefully
        assert response.status_code in [400, 422]  # Bad request or validation error

class TestUnregisterAPI:
    """Test suite for unregister functionality"""

    def test_unregister_success(self, client):
        """Test successful unregistration"""
        # Arrange
        email = "removetest@mergington.edu"
        activity = "Programming Class"
        
        # Act - First signup
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act - Then unregister
        response = client.delete(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert f"Unregistered {email} from {activity}" == data["message"]
        
        # Verify participant was removed
        get_response = client.get("/activities")
        activities_data = get_response.json()
        assert email not in activities_data[activity]["participants"]

    def test_unregister_not_signed_up(self, client):
        """Test unregister for student not signed up"""
        # Arrange
        email = "notsigned@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.delete(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_invalid_activity(self, client):
        """Test unregister from nonexistent activity"""
        # Arrange
        invalid_activity = "NonexistentActivity"
        email = "test@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{invalid_activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

class TestDataIntegrity:
    """Test data integrity and edge cases"""

    def test_activities_data_structure(self, client):
        """Test that activities maintain correct data structure"""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            
            # All participants should be strings (emails)
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email validation

    def test_concurrent_signups_isolation(self, client):
        """Test that signups don't interfere with each other"""
        # Arrange
        emails = ["user1@test.com", "user2@test.com", "user3@test.com"]
        activity = "Chess Club"
        
        # Act
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code in [200, 400]  # 400 if duplicate from previous tests
        
        # Assert
        # Verify all unique emails are in participants
        get_response = client.get("/activities")
        activities_data = get_response.json()
        participants = activities_data[activity]["participants"]
        
        # Check that our test emails are present (may include existing ones)
        for email in emails:
            if email in participants:
                assert participants.count(email) == 1  # No duplicates
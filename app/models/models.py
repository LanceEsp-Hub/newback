
# backend/app/models/models.py
from sqlalchemy import Boolean, Text, Float, Integer, String, Column, DateTime, ForeignKey, UniqueConstraint  
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB  # For PostgreSQL
from app.database.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "xxaccount_db"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    deactivated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)  # Added created_at column


    # New columns
    address_id = Column(Integer, ForeignKey('xxaddress_db.id'), nullable=True)
    notification_id = Column(Integer, ForeignKey('xxnotifications_db.id'), nullable=True)
    profile_picture = Column(Text, nullable=True)  # For base64 encoded image
    phone_number = Column(String(20), nullable=True)  # Added phone number field


    # Relationships
    address = relationship("Address", back_populates="user")
    notification_settings = relationship("Notification", back_populates="user")
    user_notifications = relationship("UserNotification", back_populates="user")
    adoption_forms = relationship("AdoptionForm", back_populates="user", cascade="all, delete-orphan")
    account_status = Column(String(20), default='active', nullable=False)  # 'active', 'suspended', 'banned'


    # Existing columns
    reset_token = Column(String, nullable=True)
    reset_token_expires_at = Column(DateTime, nullable=True)
    roles: Mapped[str] = mapped_column(String, nullable=False)

    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    devices = relationship("Device", back_populates="user")


class LoginLog(Base):
    __tablename__ = "xxlogin_logs_db"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)  # No ForeignKey needed
    email: Mapped[str] = mapped_column(String, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    attempt_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    login_metadata = Column(JSONB, nullable=True)


class AdoptionForm(Base):
    __tablename__ = "xxadoptionform_db"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('xxaccount_db.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending')  # approved/declined/pending
    
    # Applicant Information
    full_name = Column(String, nullable=False)
    contact_info = Column(String, nullable=False)
    housing_type = Column(String, nullable=False)  # own/rent
    landlord_allows_pets = Column(Boolean, nullable=True)
    
    # Household Details
    household_members = Column(JSONB, nullable=False)
    pet_allergies = Column(Boolean, nullable=False)
    allergy_types = Column(String, nullable=True)
    
    # Pet Care Plan
    primary_caregiver = Column(String, nullable=False)
    expense_responsibility = Column(String, nullable=False)
    daily_alone_time = Column(String, nullable=False)
    alone_time_plan = Column(String, nullable=True)
    emergency_care = Column(String, nullable=False)
    
    # Pet Experience
    current_pets = Column(JSONB, nullable=True)
    past_pets = Column(JSONB, nullable=True)
    past_pets_outcome = Column(String, nullable=True)
    
    # Adoption Readiness
    adoption_reason = Column(String, nullable=False)
    household_agreement = Column(Boolean, nullable=False)
    household_disagreement_reason = Column(String, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="adoption_forms")


class Address(Base):
    __tablename__ = "xxaddress_db"
    
    id = Column(Integer, primary_key=True, index=True)
    street = Column(String, nullable=False)
    barangay = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    country = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="address")


class Notification(Base):
    __tablename__ = "xxnotifications_db"
    
    id = Column(Integer, primary_key=True, index=True)
    new_messages = Column(Boolean, default=True)
    account_updates = Column(Boolean, default=True)
    pet_reminders = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)
    push_notifications = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="notification_settings")


class UserNotification(Base):
    __tablename__ = "xxuser_notifications_db"  # New table for actual notifications
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('xxaccount_db.id'), nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)
    notification_type = Column(String(50))  # e.g., "system", "security", "pet"
    related_url = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    
    user = relationship("User", back_populates="user_notifications")


class PetHealth(Base):
    __tablename__ = "xxpethealth_db"
    
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey('xxpets_db.id'), unique=True, nullable=False)
    
    # Health Information (from your form)
    vaccinated = Column(String, nullable=True)  # Could be "Yes", "No", "Unknown" etc.
    spayed_neutered = Column(String, nullable=True)  # Could be "Yes", "No", "Unknown"
    health_details = Column(Text, nullable=True)  # Free text field for health notes
    
    # Temperament & Behavior
    good_with_children = Column(Boolean, default=False)
    good_with_dogs = Column(Boolean, default=False)
    good_with_cats = Column(Boolean, default=False)
    good_with_elderly = Column(Boolean, default=False)
    good_with_strangers = Column(Boolean, default=False)
    energy_level = Column(String, nullable=True)  # e.g., "Low", "Medium", "High"
    temperament_personality = Column(Text, nullable=True)  # Free text field
    
    # Adoption Details
    reason_for_adoption = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    pet = relationship("Pet", back_populates="health_info")

class Pet(Base):
    __tablename__ = "xxpets_db"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'dog' or 'cat'
    gender = Column(String, nullable=False)  # 'male' or 'female'
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    address = Column(String, nullable=True)  # Changed from location to address
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='Safe at Home')
    image = Column(Text, nullable=True)  # For base64 image storage
    is_published = Column(Boolean, default=False)
    admin_approved = Column(Boolean, default=False)
    additional_images = Column(JSONB, nullable=True, default=list)  # For PostgreSQL


 # New column to track fingerprint generation status
    has_generated_fingerprint = Column(Boolean, default=False, nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    health_info = relationship("PetHealth", back_populates="pet", uselist=False, cascade="all, delete-orphan")
    device = relationship("Device", back_populates="pet", uselist=False, cascade="all, delete-orphan")




class Conversation(Base):
    __tablename__ = "xxconversation_db"
    
    id = Column(Integer, primary_key=True)
    user1 = Column(Integer, ForeignKey("xxaccount_db.id"), nullable=False)
    user2 = Column(Integer, ForeignKey("xxaccount_db.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships (optional)
    user1_ref = relationship("User", foreign_keys=[user1])
    user2_ref = relationship("User", foreign_keys=[user2])
    
    # Prevents duplicate conversations between the same users
    __table_args__ = (
        UniqueConstraint('user1', 'user2', name='_user_conversation_uc'),
    )


class Message(Base):
    __tablename__ = "xxmessages_db"
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("xxaccount_db.id"))
    receiver_id = Column(Integer, ForeignKey("xxaccount_db.id"))
    conversation_id = Column(Integer, ForeignKey("xxconversation_db.id"))
    text = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    conversation = relationship("Conversation", backref="messages")


# backend/app/models/models.py
class AdoptedPet(Base):
    __tablename__ = "adopted_pets"
    
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey('xxpets_db.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('xxaccount_db.id'), nullable=False)
    adopter_id = Column(Integer, ForeignKey('xxaccount_db.id'), nullable=False)
    status = Column(String, default='pending')  # pending/successful/cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)  # Add this line

    
    # Relationships
    pet = relationship("Pet")
    owner = relationship("User", foreign_keys=[owner_id])
    adopter = relationship("User", foreign_keys=[adopter_id])




class PetSimilaritySearch(Base):
    __tablename__ = "xxpet_similarity_searches_db"
    
    id = Column(Integer, primary_key=True, index=True)
    source_pet_id = Column(Integer, ForeignKey('xxpets_db.id'), nullable=False, unique=True)  # Only one record per pet
    search_timestamp = Column(DateTime, default=datetime.utcnow)
    threshold = Column(Float, nullable=False)
    max_distance = Column(String, nullable=False)
    matches_found = Column(Integer, nullable=False)
    highest_similarity_score = Column(Float, nullable=True)
    was_successful = Column(Boolean, nullable=False)
    total_searches = Column(Integer, default=1)  # Track how many times searched
    
    # Relationships
    source_pet = relationship("Pet", foreign_keys=[source_pet_id])


class SuccessStory(Base):
    __tablename__ = "xxsuccess_stories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    cat_name: Mapped[str] = mapped_column(String, nullable=False)
    story: Mapped[str] = mapped_column(Text, nullable=False)
    image_filenames: Mapped[list] = mapped_column(JSONB, nullable=False)  # Stores list of image filenames
    created_at = Column(DateTime, default=datetime.utcnow)

class UserReport(Base):
    __tablename__ = "user_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("xxaccount_db.id"), nullable=False)
    reported_user_id = Column(Integer, ForeignKey("xxaccount_db.id"), nullable=False)
    reason = Column(String(50), nullable=False)  # harassment, spam, inappropriate_content, fake_profile, other
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, reviewed, resolved, dismissed
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("xxaccount_db.id"), nullable=True)
    
    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

class BlockedUser(Base):
    __tablename__ = "blocked_users"
    
    id = Column(Integer, primary_key=True, index=True)
    blocker_id = Column(Integer, ForeignKey("xxaccount_db.id"), nullable=False)
    blocked_user_id = Column(Integer, ForeignKey("xxaccount_db.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    blocker = relationship("User", foreign_keys=[blocker_id])
    blocked_user = relationship("User", foreign_keys=[blocked_user_id])



class Device(Base):
    __tablename__ = "xxdevice_db"
    
    device_id = Column(Integer, primary_key=True, index=True)
    unique_code = Column(String(50), unique=True, nullable=False)  # e.g. "LILYGO-7A83-B2"
    pet_id = Column(Integer, ForeignKey('xxpets_db.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('xxaccount_db.id'), nullable=True)
    is_active = Column(Boolean, default=False)
    paired_at = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    is_online = Column(Boolean, default=False)
    
    # Relationships
    pet = relationship("Pet", back_populates="device")
    user = relationship("User", back_populates="devices")
    locations = relationship("Location", back_populates="device", cascade="all, delete-orphan")

class Location(Base):
    __tablename__ = "xxlocation_db"
    
    location_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('xxdevice_db.device_id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    device = relationship("Device", back_populates="locations")

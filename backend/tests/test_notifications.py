"""Tests for email notification service (logs only, no SMTP in tests)."""

import logging

from app.services.notifications import (
    notify_booking_request,
    notify_booking_status,
    notify_new_message,
    send_email,
)


def test_send_email_logs_when_no_smtp(caplog):
    """Without SMTP configured, emails should be logged."""
    with caplog.at_level(logging.INFO):
        result = send_email("user@example.com", "Test Subject", "Test body")
    assert result is False
    assert "user@example.com" in caplog.text
    assert "Test Subject" in caplog.text


def test_notify_new_message(caplog):
    with caplog.at_level(logging.INFO):
        notify_new_message("bob@test.com", "Alice")
    assert "bob@test.com" in caplog.text
    assert "Alice" in caplog.text


def test_notify_booking_request(caplog):
    with caplog.at_level(logging.INFO):
        notify_booking_request("owner@test.com", "Bob", "Electric Drill")
    assert "owner@test.com" in caplog.text
    assert "Electric Drill" in caplog.text


def test_notify_booking_status(caplog):
    with caplog.at_level(logging.INFO):
        notify_booking_status("borrower@test.com", "Ladder", "approved")
    assert "borrower@test.com" in caplog.text
    assert "approved" in caplog.text

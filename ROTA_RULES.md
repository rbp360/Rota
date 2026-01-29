# Rota AI Agent Rules

This document outlines the business rules for determining teacher availability and cover eligibility in the Rota system. These rules must be respected by the AI agent and implemented in the system's normalization and availability logic.

## 1. Specialist vs. Form Teacher Availability

The primary rule is that form teachers are often "free" even when their timetable shows an activity, if that activity is a specialist lesson taught by someone else.

### Freeing Keywords for Form Teachers
If a **form teacher** (not a specialist) has any of the following in their activity, they are considered **AVAILABLE** for cover:
- **Thai** (any derivative: "Thai Language", "Thai Culture", etc.)
- **Music**
- **PE** (any spelling/derivative: "P.E.", "Physical Education", etc.)
- **PHSE** (Personal, Health, Social and Economic education)

**Reasoning:** These lessons are taught by specialist teachers (e.g., Daryl for Music, Billy for PE). The students attend these lessons, but the form teacher does not teach them, and is therefore free to provide cover.

### Specialist Teachers
The following staff are designated as **Specialists**. They are rarely "free" unless explicitly marked:
- **Daryl** (Music)
- **Becky** (Drama)
- **Billy** (PE)
- **Jinny / Ginny** (Assistant)
- **Ben** (Forest School)
- **Faye** (Cover Specialist)
- **Claire** (Head of School)
- **Jake** (Assistant)
- **Retno** (Pre-nursery)
- **Jacinta** (Nursery)

## 2. Availability Display Rules
When a teacher is determined to be free because their class is with a specialist, the UI should display the reason.
- **Example:** If Rosie is free because her class (6 RG) has Music, the availability list should show: "6 RG doing Music".

## 3. Specialist Priority
- **Specialists** who are busy should generally still be shown in the availability list but highlighted in red (as "Busy") to allow for emergency overriding if necessary.
- **Form Teachers** who are truly busy (teaching their own class) should be hidden from the availability list to reduce clutter.
- **Form Teachers** who are free (due to Specialist lessons) should be shown clearly.

## 4. Priority Staff
- **Claire** (Head of School) is a priority staff member. She should be highlighted when free, but only used if necessary.

# Business Requirements Document (Cascade Freight Systems – Secure Chatbot)

## Section 1.0 Login
| ID   | Requirement              | Description                                                      |
|------|--------------------------|------------------------------------------------------------------|
| 1.0  | Login                    | Secure authentication before accessing chatbot features.         |
| 1.1  | Create an Account        | New employees can register with role‑based access.               |
| 1.1.1| Role Assignment          | Access level assigned during account creation (dispatcher, driver, support staff). |
| 1.2  | Forgot Password          | Users can reset credentials securely through internal verification. |
| 1.3  | Session Management       | System enforces timeouts and secure logout to prevent unauthorized access. |
| 1.4  | Terms & Conditions       | Users must accept Cascade Freight’s internal use policy before accessing the chatbot. |
| 1.5  | Privacy Notice           | Entry page displays a statement on how employee data is protected. |
| 1.6  | Multi‑Factor Authentication | Requires a second verification step (e.g., code via internal system) for all 20 users. |

## Section 2.0 Dispatch Coordination
| ID   | Requirement              | Description                                                      |
|------|--------------------------|------------------------------------------------------------------|
| 2.0  | Dispatch Coordination    | Chatbot provides quick answers about driver locations and shipment status. |
| 2.1  | Driver Lookup            | Dispatcher can query driver’s current assignment and location.   |
| 2.1.1| Active Driver Status     | Returns whether driver is on duty, en route, or idle.            |
| 2.1.2| Location Query           | Provides driver’s last known location from internal GPS/logs.    |
| 2.2  | Shipment Status          | Dispatcher can query the status of any shipment.                 |
| 2.2.1| Real‑Time Updates        | Pulls current shipment progress from internal database.          |
| 2.2.2| Exception Alerts         | Flags delays, reroutes, or issues automatically.                 |
| 2.3  | Assignment Management    | Dispatcher can confirm or update driver‑shipment assignments.    |
| 2.3.1| Reassignment Requests    | Allows dispatcher to reassign shipments securely.                |
| 2.3.2| Confirmation Logging     | Records assignment changes for audit purposes.                   |

## Section 3.0 Shipment Tracking
| ID   | Requirement              | Description                                                      |
|------|--------------------------|------------------------------------------------------------------|
| 3.0  | Shipment Tracking        | Chatbot provides real‑time shipment information to dispatchers and support staff. |
| 3.1  | Status Query             | Users can request the current status of any shipment.            |
| 3.1.1| In‑Transit Updates       | Displays whether shipment is pending, in transit, or delivered.  |
| 3.1.2| Delivery Confirmation    | Confirms when shipment has been successfully delivered.          |
| 3.2  | ETA Updates              | Provides estimated arrival times based on current route and conditions. |
| 3.2.1| Dynamic ETA Adjustments  | Updates ETA automatically if delays or reroutes occur.           |
| 3.3  | Exception Alerts         | Flags issues such as delays, reroutes, or damaged goods.         |
| 3.3.1| Delay Notifications      | Notifies dispatcher when shipment is behind schedule.            |
| 3.3.2| Route Change Alerts      | Reports if shipment has been rerouted.                           |
| 3.4  | Historical Tracking      | Allows users to view past shipment records for audit and reporting. |

## Section 4.0 Employee Support
| ID   | Requirement              | Description                                                      |
|------|--------------------------|------------------------------------------------------------------|
| 4.0  | Employee Support         | Chatbot provides staff with quick answers to common questions and resources. |
| 4.1  | Policy Queries           | Employees can ask about company policies (e.g., safety, HR, scheduling). |
| 4.1.1| HR Policies              | Returns answers about vacation, sick leave, and benefits.        |
| 4.1.2| Safety Policies          | Provides guidance on freight handling and compliance rules.      |
| 4.2  | Contact Directory        | Chatbot returns contact information for staff and departments.   |
| 4.2.1| Department Lookup        | Provides phone/email for specific departments (dispatch, HR, IT).|
| 4.2.2| Individual Lookup        | Returns contact details for specific employees.                  |
| 4.3  | Scheduling Support       | Employees can query shift schedules or driver assignments.       |
| 4.3.1| Shift Lookup             | Displays upcoming shifts for employees.                          |
| 4.3.2| Assignment Lookup        | Shows which driver is assigned to which shipment.                |
| 4.4  | FAQ Responses            | Chatbot answers frequently asked questions to reduce repetitive support requests. |

## Section 5.0 Role-Based Access
| ID   | Requirement              | Description                                                      |
|------|--------------------------|------------------------------------------------------------------|
| 5.0  | Role-Based Access        | Chatbot enforces permissions based on employee role.             |
| 5.1  | Dispatcher Access        | Dispatchers can query drivers, shipments, and assignments.       |
| 5.2  | Driver Access            | Drivers can view their own assignments and schedules only.       |
| 5.3  | Support Staff Access     | Support staff can query policies, FAQs, and contact directory.   |
| 5.4  | Admin Access             | Admins can manage accounts, roles, and audit logs.               |

## Section 6.0 Audit Logging
| ID   | Requirement              | Description                                                      |
|------|--------------------------|------------------------------------------------------------------|
| 6.0  | Audit Logging            | System records all chatbot interactions for compliance review.   |
| 6.1  | Login Events             | Logs successful and failed login attempts.                       |
| 6.2  | Assignment Changes       | Records shipment reassignments and confirmations.                |
| 6.3  | Policy Queries           | Tracks employee queries about HR and safety policies.            |
| 6.4  | Exception Alerts         | Logs all flagged shipment issues for later review.               |

## Section 7.0 Security
| ID   | Requirement              | Description                                                      |
|------|--------------------------|------------------------------------------------------------------|
| 7.0  | Security                 | Chatbot enforces Cascade Freight’s internal security standards.  |
| 7.1  | Data Encryption          | All data in transit and at rest is encrypted.                    |
| 7.2  | Token Management         | Tokens are stored securely and never exposed in production UI.   |
| 7.3  | Session Timeout          | Sessions expire after inactivity to prevent unauthorized use.    |
| 7.4  | Internal Network Access  | Chatbot is accessible only within Cascade Freight’s internal network. |

## Section 8.0 Scalability
| ID   | Requirement              | Description                                                      |
|------|--------------------------|------------------------------------------------------------------|
| 8.0  | Scalability              | Chatbot supports growth in users and shipments.                  |
| 8.1  | Concurrent Users         | System supports up to 20 concurrent authenticated users.         |
| 8.2  | Database Performance     | Queries return results within 2 seconds under normal load.       |
| 8.3  | Horizontal Scaling       | Architecture allows scaling across multiple servers.             |

## Section 9.0 Usability
| ID   | Requirement              | Description                                                      |
|------|--------------------------|------------------------------------------------------------------|
| 9.0  | Usability                | Chatbot provides intuitive and accessible interface.             |
| 9.1  | Responsive Design        | Works across desktop and mobile devices.                         |
| 9.2  | Accessibility            | Meets WCAG 2.1 AA accessibility standards.                       |
| 9.3  | Clear Feedback           | Provides confirmation messages for actions (login, assignment changes). |
| 9.4  | Error Handling           | Displays user-friendly error messages for invalid inputs.        |

## Section 10.0 Reliability
| ID   | Requirement              | Description                                                      |
|------|--------------------------|------------------------------------------------------------------|
| 10.0 | Reliability              | Chatbot maintains consistent availability and performance.       |
| 10.1 | Uptime                   | System uptime target is 99.5%.                                   |
| 10.2 | Failover Support         | System recovers automatically from server failures.              |
| 10.3 | Backup & Restore         | Daily backups with ability to restore within 2 hours.            |
| 10.4 | Monitoring               | System health monitored continuously with alerts for downtime.   |

# Database Diagram

Dưới đây là mô tả DB diagram theo định dạng DBML cho `Server_service`.

```dbml
Table users {
  id varchar [pk]
  email varchar [unique, not null]
  full_name varchar [not null]
  password_hash varchar
  public_profile text
  avatar_url varchar
  default_organization_id varchar
  locale varchar [not null, default: 'vi']
  timezone varchar [not null, default: 'Asia/Saigon']
  is_active boolean [not null, default: true]
  created_at datetime [not null]
}

Table organizations {
  id varchar [pk]
  name varchar [not null]
  industry varchar
  description text
  sensitive_restrictions text
  billing_plan varchar [not null, default: 'free']
  billing_status varchar [not null, default: 'trialing']
  settings_json text [not null, default: '{}']
  created_at datetime [not null]
}

Table organization_members {
  id varchar [pk]
  user_id varchar [ref: > users.id]
  organization_id varchar [ref: > organizations.id]
  role varchar [not null, default: 'user']
  permissions text [not null, default: '[]']
  status varchar [not null, default: 'active']
  joined_at datetime [not null]
}

Table documents {
  id varchar [pk]
  organization_id varchar [ref: > organizations.id]
  uploaded_by_user_id varchar [ref: > users.id]
  file_name varchar [not null]
  source_url varchar [not null]
  status varchar [not null, default: 'processing']
  chunk_count varchar [not null, default: '0']
  embedding_model varchar [not null, default: 'text-embedding-3-small']
  vector_index varchar
  metadata_json text [not null, default: '{}']
  created_at datetime [not null]
  updated_at datetime [not null]
}

Table pipeline_events {
  id varchar [pk]
  organization_id varchar [ref: > organizations.id]
  document_id varchar [ref: > documents.id]
  actor_user_id varchar [ref: > users.id]
  stage varchar [not null]
  status varchar [not null]
  message text
  created_at datetime [not null]
}

Table chat_sessions {
  id varchar [pk]
  organization_id varchar [ref: > organizations.id]
  user_id varchar [ref: > users.id]
  context_type varchar [not null, default: 'organization']
  title varchar [not null]
  is_pinned boolean [not null, default: false]
  created_at datetime [not null]
  updated_at datetime [not null]
}

Table chat_messages {
  id varchar [pk]
  session_id varchar [ref: > chat_sessions.id]
  sender_type varchar [not null]
  content text [not null]
  citations_json text [not null, default: '[]']
  created_at datetime [not null]
}

Table chat_feedback {
  id varchar [pk]
  message_id varchar [ref: > chat_messages.id]
  user_id varchar [ref: > users.id]
  rating varchar [not null]
  comment text
  created_at datetime [not null]
}

Table notifications {
  id varchar [pk]
  user_id varchar [ref: > users.id]
  organization_id varchar [ref: > organizations.id]
  notification_type varchar [not null, default: 'system']
  title varchar [not null]
  content text
  action_url varchar
  is_read boolean [not null, default: false]
  created_at datetime [not null]
}

Table billing_records {
  id varchar [pk]
  organization_id varchar [ref: > organizations.id]
  created_by_user_id varchar [ref: > users.id]
  plan varchar [not null]
  status varchar [not null, default: 'pending']
  amount varchar [not null, default: '0']
  currency varchar [not null, default: 'VND']
  provider varchar [not null, default: 'manual']
  provider_reference varchar
  created_at datetime [not null]
}

Ref: users.id < organization_members.user_id
Ref: organizations.id < organization_members.organization_id
Ref: organizations.id < documents.organization_id
Ref: users.id < documents.uploaded_by_user_id
Ref: organizations.id < pipeline_events.organization_id
Ref: documents.id < pipeline_events.document_id
Ref: users.id < pipeline_events.actor_user_id
Ref: organizations.id < chat_sessions.organization_id
Ref: users.id < chat_sessions.user_id
Ref: chat_sessions.id < chat_messages.session_id
Ref: chat_messages.id < chat_feedback.message_id
Ref: users.id < chat_feedback.user_id
Ref: users.id < notifications.user_id
Ref: organizations.id < notifications.organization_id
Ref: organizations.id < billing_records.organization_id
Ref: users.id < billing_records.created_by_user_id
```

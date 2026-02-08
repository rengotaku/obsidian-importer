---
title: Online DDL of MySQL
date: 2022-10-17
tags:
  - mysql
  - database
categories:
  - engineering
keywords:
  - ddl
  - schema-migration
layout: post
permalink: /2022/10/online-ddl-mysql/
slug: online-ddl-mysql
lastmod: 2023-01-15
---

## Introduction

Online DDL (Data Definition Language) in MySQL allows schema changes without blocking concurrent DML operations.

### Key Features

- **ALGORITHM=INPLACE**: Changes metadata without copying the entire table
- **ALGORITHM=COPY**: Creates a temporary table and copies data
- **LOCK=NONE**: Allows concurrent reads and writes during DDL

### Example

```sql
ALTER TABLE users ADD COLUMN email VARCHAR(255), ALGORITHM=INPLACE, LOCK=NONE;
```

### Best Practices

1. Always test DDL changes on a staging environment first
2. Monitor replication lag during large table alterations
3. Use pt-online-schema-change for very large tables

#mysql #performance

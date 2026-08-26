---
question_id: "1903aded"
session_index: 28
session_id: "sharegpt_5QjRckj_0"
timestamp: "2023/05/26 (Fri) 10:09"
is_evidence_session: false
turn_count: 8
translation_status: TODO
---
# Session 028 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
Hi! what architectures and stack can I use to create an ad-hoc reporting capability in a SaaS product that uses AWS Aurora Postgres database? My main concerns are ensuring data security and performance. I need the ad-hoc reporting capability to be performant without affecting the operational database.
<!-- SOURCE_TURN_000_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_000_BEGIN -->
嗨！我可以使用哪些架构和技术栈来在基于 AWS Aurora Postgres 数据库的 SaaS 产品中创建临时报告功能？我主要关心的是确保数据安全性和性能。我需要临时报告功能在不影响运营数据库的情况下保持高性能。
<!-- ZH_TURN_000_END -->

## Turn 001 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_001_BEGIN -->
For the ad-hoc reporting capability in your SaaS product, you can consider using the following stack:

* Data Warehouse: You can set up a data warehouse using Amazon Redshift, which is a fully managed, petabyte-scale data warehouse service. This will allow you to have a separate reporting environment that does not affect your operational database.
* ETL pipeline: Use AWS Glue or Apache Airflow to extract data from the Aurora Postgres database, transform it into a format suitable for reporting, and load it into the data warehouse.
* BI Tool: You can use Amazon QuickSight, which is a fast, cloud-powered business intelligence service, to create interactive visualizations, reports, and dashboards.
* Security: To ensure data security, you can use Amazon VPC to set up a virtual private cloud for your data warehouse and BI tool, which will allow you to secure network access and control data flow. You can also use AWS IAM to manage access to your data and services.

This architecture will allow you to have a secure and performant ad-hoc reporting capability for your SaaS product while ensuring that the operational database is not affected.
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
对于您的 SaaS 产品中的临时报告功能，您可以考虑使用以下技术栈：

* 数据仓库：您可以使用 Amazon Redshift 设置数据仓库，这是一个完全托管、PB 级的数据仓库服务。这将使您拥有一个独立的报告环境，不会影响您的运营数据库。
* ETL 管道：使用 AWS Glue 或 Apache Airflow 从 Aurora Postgres 数据库提取数据，将其转换为适合报告的格式，并加载到数据仓库中。
* BI 工具：您可以使用 Amazon QuickSight，这是一个快速、云驱动的商业智能服务，用于创建交互式可视化、报告和仪表板。
* 安全性：为确保数据安全，您可以使用 Amazon VPC 为您的数据仓库和 BI 工具设置虚拟私有云，这将允许您保护网络访问并控制数据流。您还可以使用 AWS IAM 管理对数据和服务的访问。

这种架构将使您能够为 SaaS 产品提供安全且高性能的临时报告功能，同时确保运营数据库不受影响。
<!-- ZH_TURN_001_END -->

## Turn 002 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_002_BEGIN -->
Using an ETL pipeline will result in a delay in getting data from Aurora postgres into redshift, right? I need real time. Or at least near real time.
<!-- SOURCE_TURN_002_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_002_BEGIN -->
使用 ETL 管道会导致从 Aurora Postgres 获取数据到 Redshift 时出现延迟，对吗？我需要实时数据。或者至少是接近实时的。
<!-- ZH_TURN_002_END -->

## Turn 003 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_003_BEGIN -->
Using an ETL pipeline with a data warehouse like Redshift will indeed result in a delay in getting data from Aurora Postgres. If you need near real-time data for your ad-hoc reporting, there are a few approaches you can consider:

1. Materialized views: You can create materialized views in Aurora Postgres that pre-aggregate the data you need for reporting. This way, you can reduce the amount of data you need to transfer to the data warehouse and speed up the reporting process.
2. Direct Connect: You can use Amazon Direct Connect to set up a dedicated network connection between your Aurora Postgres database and your Redshift cluster, which will reduce the latency in data transfer.
3. Replication: You can set up replication from Aurora Postgres to Redshift using Amazon Database Migration Service (DMS) or Amazon AppFlow. This will allow you to keep the data in Redshift in near real-time sync with the data in Aurora Postgres.
4. In-memory cache: You can use Amazon ElastiCache for Redis or Amazon DynamoDB to store the data from Aurora Postgres in an in-memory cache. This will allow you to have fast access to the data without having to query the database.

Each of these approaches has its own trade-offs in terms of complexity, cost, and data freshness. You'll need to evaluate your specific requirements to determine which approach works best for your use case.
<!-- SOURCE_TURN_003_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_003_BEGIN -->
使用带有数据仓库（如 Redshift）的 ETL 管道确实会导致从 Aurora Postgres 获取数据时出现延迟。如果您需要接近实时的数据用于临时报告，您可以考虑以下几种方法：

1. 物化视图：您可以在 Aurora Postgres 中创建物化视图，预先聚合您需要的报告数据。这样，您可以减少需要传输到数据仓库的数据量，并加快报告过程。
2. Direct Connect：您可以使用 Amazon Direct Connect 在 Aurora Postgres 数据库和 Redshift 集群之间设置专用网络连接，这将减少数据传输的延迟。
3. 复制：您可以使用 Amazon Database Migration Service (DMS) 或 Amazon AppFlow 设置从 Aurora Postgres 到 Redshift 的复制。这将使 Redshift 中的数据与 Aurora Postgres 中的数据保持接近实时的同步。
4. 内存缓存：您可以使用 Amazon ElastiCache for Redis 或 Amazon DynamoDB 将 Aurora Postgres 中的数据存储在内存缓存中。这将使您无需查询数据库即可快速访问数据。

每种方法在复杂性、成本和数据新鲜度方面都有各自的权衡。您需要评估您的具体需求，以确定哪种方法最适合您的用例。
<!-- ZH_TURN_003_END -->

## Turn 004 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_004_BEGIN -->
About option 3 (replication), can I set up the replication in such a way that only some tables and/or columns are replicated?
<!-- SOURCE_TURN_004_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_004_BEGIN -->
关于选项 3（复制），我可以设置复制方式，使其只复制某些表和/或列吗？
<!-- ZH_TURN_004_END -->

## Turn 005 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_005_BEGIN -->
Yes, you can set up replication from Aurora Postgres to Redshift in such a way that only some tables and/or columns are replicated. This can be done using Amazon Database Migration Service (DMS) or Amazon AppFlow.

With DMS, you can create a migration task that specifies the tables and columns you want to replicate. You can also set up filters to only replicate the data that meets certain criteria.

With AppFlow, you can set up a flow that replicates only specific tables and columns from Aurora Postgres to Redshift. You can also use AppFlow's data transformation capabilities to modify the data during the replication process.

By replicating only the tables and columns you need for reporting, you can reduce the amount of data transferred and improve the performance of your replication process.
<!-- SOURCE_TURN_005_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_005_BEGIN -->
是的，您可以设置从 Aurora Postgres 到 Redshift 的复制，使其只复制某些表和/或列。这可以通过 Amazon Database Migration Service (DMS) 或 Amazon AppFlow 实现。

使用 DMS，您可以创建指定要复制的表和列的迁移任务。您还可以设置过滤器，只复制满足特定条件的数据。

使用 AppFlow，您可以设置一个流，只从 Aurora Postgres 复制特定表和列到 Redshift。您还可以使用 AppFlow 的数据转换功能在复制过程中修改数据。

通过只复制您需要的表和列用于报告，您可以减少传输的数据量，并提高复制过程的性能。
<!-- ZH_TURN_005_END -->

## Turn 006 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_006_BEGIN -->
Cool! How can that migration task triggered? Can run (and so replicate the data) every time data in certain tables is changed?
<!-- SOURCE_TURN_006_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_006_BEGIN -->
太棒了！那个迁移任务如何触发？它可以在某些表中的数据每次更改时运行（并因此复制数据）吗？
<!-- ZH_TURN_006_END -->

## Turn 007 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_007_BEGIN -->
Yes, the migration task created using Amazon Database Migration Service (DMS) can be triggered to run every time data in certain tables is changed. This is usually done through change data capture (CDC), which captures the changes to the data in the source database (Aurora Postgres) and applies those changes to the target database (Redshift).

Here's how you can set up CDC in DMS:

1. Enable CDC on the source database: You'll need to enable CDC on the Aurora Postgres database to capture the changes to the data. This can usually be done by enabling a CDC option in the database configuration or by using a plugin provided by the database vendor.
2. Create a DMS replication instance: You'll need to create a DMS replication instance, which is a managed service that will perform the actual replication.
3. Create a DMS task: You'll need to create a DMS task, which specifies the source and target databases, the tables you want to replicate, and other configuration options such as filters and transformations. You'll also need to select CDC as the replication method for the task.
4. Start the DMS task: Once you've set up the task, you can start it and the replication process will begin. DMS will continuously capture the changes to the data in the source database and apply those changes to the target database.

By setting up CDC in DMS, you can ensure that the data in Redshift is in near real-time sync with the data in Aurora Postgres. This will allow you to have up-to-date data for your ad-hoc reporting needs.
<!-- SOURCE_TURN_007_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_007_BEGIN -->
是的，使用 Amazon Database Migration Service (DMS) 创建的迁移任务可以设置为在特定表中的数据每次更改时触发运行。这通常通过变更数据捕获 (CDC) 实现，它捕获源数据库（Aurora Postgres）中的数据更改，并将这些更改应用到目标数据库（Redshift）。

以下是如何在 DMS 中设置 CDC 的方法：

1. 在源数据库上启用 CDC：您需要在 Aurora Postgres 数据库上启用 CDC 以捕获数据更改。这通常可以通过在数据库配置中启用 CDC 选项或使用数据库供应商提供的插件来完成。
2. 创建 DMS 复制实例：您需要创建一个 DMS 复制实例，这是一个托管服务，将执行实际的复制。
3. 创建 DMS 任务：您需要创建一个 DMS 任务，该任务指定源和目标数据库、要复制的表以及其他配置选项，如过滤器和转换。您还需要为任务选择 CDC 作为复制方法。
4. 启动 DMS 任务：设置好任务后，您可以启动它，复制过程将开始。DMS 将连续捕获源数据库中的数据更改，并将这些更改应用到目标数据库。

通过在 DMS 中设置 CDC，您可以确保 Redshift 中的数据与 Aurora Postgres 中的数据保持接近实时的同步。这将使您能够为临时报告需求提供最新的数据。
<!-- ZH_TURN_007_END -->

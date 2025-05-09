--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY "public"."supplier" DROP CONSTRAINT IF EXISTS "supplier_user_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."skualias" DROP CONSTRAINT IF EXISTS "skualias_user_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."skualias" DROP CONSTRAINT IF EXISTS "skualias_canonical_sku_fkey";
ALTER TABLE IF EXISTS ONLY "public"."sale" DROP CONSTRAINT IF EXISTS "sale_user_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."sale" DROP CONSTRAINT IF EXISTS "sale_product_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."purchaseorderitem" DROP CONSTRAINT IF EXISTS "purchaseorderitem_product_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."purchaseorderitem" DROP CONSTRAINT IF EXISTS "purchaseorderitem_po_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."purchaseorder" DROP CONSTRAINT IF EXISTS "purchaseorder_supplier_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."purchaseorder" DROP CONSTRAINT IF EXISTS "purchaseorder_created_by_fkey";
ALTER TABLE IF EXISTS ONLY "public"."product" DROP CONSTRAINT IF EXISTS "product_user_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."product" DROP CONSTRAINT IF EXISTS "product_supplier_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."notification" DROP CONSTRAINT IF EXISTS "notification_user_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."inventoryledger" DROP CONSTRAINT IF EXISTS "inventoryledger_product_id_fkey";
ALTER TABLE IF EXISTS ONLY "public"."connector" DROP CONSTRAINT IF EXISTS "connector_created_by_fkey";
DROP INDEX IF EXISTS "public"."ix_user_email";
DROP INDEX IF EXISTS "public"."ix_supplier_name";
DROP INDEX IF EXISTS "public"."ix_skualias_alias_sku";
DROP INDEX IF EXISTS "public"."ix_purchaseorder_supplier_id";
DROP INDEX IF EXISTS "public"."ix_purchaseorder_status";
DROP INDEX IF EXISTS "public"."ix_product_sku";
DROP INDEX IF EXISTS "public"."ix_product_name";
DROP INDEX IF EXISTS "public"."ix_inventoryledger_source";
ALTER TABLE IF EXISTS ONLY "public"."user" DROP CONSTRAINT IF EXISTS "user_pkey";
ALTER TABLE IF EXISTS ONLY "public"."supplier" DROP CONSTRAINT IF EXISTS "supplier_pkey";
ALTER TABLE IF EXISTS ONLY "public"."skualias" DROP CONSTRAINT IF EXISTS "skualias_pkey";
ALTER TABLE IF EXISTS ONLY "public"."sale" DROP CONSTRAINT IF EXISTS "sale_pkey";
ALTER TABLE IF EXISTS ONLY "public"."purchaseorderitem" DROP CONSTRAINT IF EXISTS "purchaseorderitem_pkey";
ALTER TABLE IF EXISTS ONLY "public"."purchaseorder" DROP CONSTRAINT IF EXISTS "purchaseorder_pkey";
ALTER TABLE IF EXISTS ONLY "public"."product" DROP CONSTRAINT IF EXISTS "product_pkey";
ALTER TABLE IF EXISTS ONLY "public"."notification" DROP CONSTRAINT IF EXISTS "notification_pkey";
ALTER TABLE IF EXISTS ONLY "public"."inventoryledger" DROP CONSTRAINT IF EXISTS "inventoryledger_pkey";
ALTER TABLE IF EXISTS ONLY "public"."connector" DROP CONSTRAINT IF EXISTS "connector_pkey";
DROP TABLE IF EXISTS "public"."user";
DROP TABLE IF EXISTS "public"."supplier";
DROP TABLE IF EXISTS "public"."skualias";
DROP TABLE IF EXISTS "public"."sale";
DROP TABLE IF EXISTS "public"."purchaseorderitem";
DROP TABLE IF EXISTS "public"."purchaseorder";
DROP TABLE IF EXISTS "public"."product";
DROP TABLE IF EXISTS "public"."notification";
DROP TABLE IF EXISTS "public"."inventoryledger";
DROP TABLE IF EXISTS "public"."connector";
DROP TYPE IF EXISTS "public"."userrole";
DROP TYPE IF EXISTS "public"."postatus";
DROP TYPE IF EXISTS "public"."notificationchannel";
DROP TYPE IF EXISTS "public"."connectorprovider";
DROP TYPE IF EXISTS "public"."alertlevel";
--
-- Name: SCHEMA "public"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA "public" IS 'standard public schema';


--
-- Name: alertlevel; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE "public"."alertlevel" AS ENUM (
    'RED',
    'YELLOW'
);


--
-- Name: connectorprovider; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE "public"."connectorprovider" AS ENUM (
    'SHOPIFY',
    'SQUARE',
    'LIGHTSPEED',
    'CSV'
);


--
-- Name: notificationchannel; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE "public"."notificationchannel" AS ENUM (
    'EMAIL',
    'IN_APP',
    'SMS'
);


--
-- Name: postatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE "public"."postatus" AS ENUM (
    'DRAFT',
    'SENT',
    'RECEIVED'
);


--
-- Name: userrole; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE "public"."userrole" AS ENUM (
    'OWNER',
    'MANAGER',
    'STAFF'
);


SET default_tablespace = '';

SET default_table_access_method = "heap";

--
-- Name: connector; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."connector" (
    "id" "uuid" NOT NULL,
    "provider" "public"."connectorprovider" NOT NULL,
    "access_token" character varying NOT NULL,
    "refresh_token" character varying,
    "expires_at" timestamp without time zone,
    "status" character varying NOT NULL,
    "created_by" "uuid" NOT NULL,
    "last_sync" timestamp without time zone
);


--
-- Name: inventoryledger; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."inventoryledger" (
    "id" "uuid" NOT NULL,
    "product_id" "uuid" NOT NULL,
    "quantity_delta" integer NOT NULL,
    "quantity_after" integer NOT NULL,
    "source" character varying NOT NULL,
    "reference_id" character varying,
    "timestamp" timestamp without time zone NOT NULL
);


--
-- Name: notification; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."notification" (
    "id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "channel" "public"."notificationchannel" NOT NULL,
    "payload" json,
    "sent_at" timestamp without time zone,
    "read_at" timestamp without time zone
);


--
-- Name: product; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."product" (
    "id" "uuid" NOT NULL,
    "sku" character varying NOT NULL,
    "name" character varying NOT NULL,
    "variant" character varying,
    "supplier_id" "uuid",
    "cost" double precision NOT NULL,
    "on_hand" integer NOT NULL,
    "reorder_point" integer NOT NULL,
    "safety_stock" integer NOT NULL,
    "lead_time_days" integer NOT NULL,
    "created_at" timestamp without time zone NOT NULL,
    "alert_level" "public"."alertlevel",
    "user_id" "uuid" NOT NULL
);


--
-- Name: purchaseorder; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."purchaseorder" (
    "id" "uuid" NOT NULL,
    "supplier_id" "uuid" NOT NULL,
    "status" "public"."postatus" NOT NULL,
    "created_by" "uuid" NOT NULL,
    "pdf_url" character varying,
    "created_at" timestamp without time zone NOT NULL,
    "updated_at" timestamp without time zone NOT NULL
);


--
-- Name: purchaseorderitem; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."purchaseorderitem" (
    "id" "uuid" NOT NULL,
    "po_id" "uuid" NOT NULL,
    "product_id" "uuid" NOT NULL,
    "quantity" integer NOT NULL,
    "unit_cost" double precision NOT NULL
);


--
-- Name: sale; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."sale" (
    "id" "uuid" NOT NULL,
    "product_id" "uuid" NOT NULL,
    "quantity" integer NOT NULL,
    "sale_date" timestamp without time zone NOT NULL,
    "notes" character varying,
    "user_id" "uuid" NOT NULL
);


--
-- Name: skualias; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."skualias" (
    "id" "uuid" NOT NULL,
    "alias_sku" character varying NOT NULL,
    "canonical_sku" character varying NOT NULL,
    "notes" character varying,
    "created_at" timestamp without time zone NOT NULL,
    "user_id" "uuid" NOT NULL
);


--
-- Name: supplier; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."supplier" (
    "id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "contact_email" character varying NOT NULL,
    "phone" character varying,
    "lead_time_days" integer NOT NULL,
    "notes" character varying,
    "created_at" timestamp without time zone NOT NULL,
    "user_id" "uuid" NOT NULL
);


--
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "public"."user" (
    "id" "uuid" NOT NULL,
    "email" character varying NOT NULL,
    "password_hash" character varying NOT NULL,
    "role" "public"."userrole" NOT NULL,
    "created_at" timestamp without time zone NOT NULL
);


--
-- Data for Name: connector; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."connector" ("id", "provider", "access_token", "refresh_token", "expires_at", "status", "created_by", "last_sync") FROM stdin;
\.


--
-- Data for Name: inventoryledger; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."inventoryledger" ("id", "product_id", "quantity_delta", "quantity_after", "source", "reference_id", "timestamp") FROM stdin;
f8513f9c-a3e0-4887-8c18-d97942854641	a78646b4-c01a-49fd-a91a-9382d11440a9	10	12	manual	\N	2025-05-07 00:13:23.527864
\.


--
-- Data for Name: notification; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."notification" ("id", "user_id", "channel", "payload", "sent_at", "read_at") FROM stdin;
\.


--
-- Data for Name: product; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."product" ("id", "sku", "name", "variant", "supplier_id", "cost", "on_hand", "reorder_point", "safety_stock", "lead_time_days", "created_at", "alert_level", "user_id") FROM stdin;
5555f7a4-20eb-4c66-963f-c2ed91cac445	001	Lava Candle	\N	5fd0dc55-42e3-4bae-b193-f082f97ea505	10	4	3	0	7	2025-05-06 20:17:30.292616	\N	ec3a64e4-08e2-41e5-9b3a-16cdb5dfaeb0
c9d3c7b2-9ede-4b59-b84a-298d13b08833	123	Lantern	\N	5819d228-c3b6-467c-97e5-dd8969edb4db	120	10	10	5	7	2025-05-06 22:43:54.848669	YELLOW	c13a7b3a-2c84-4e11-8040-e8b5d9c1ec65
a78646b4-c01a-49fd-a91a-9382d11440a9	SHIRT-BLK-M	Black T-Shirt	\N	04f57042-3a0a-480e-9870-ee0e5381e8e3	15	12	2	0	7	2025-05-06 23:59:12.187797	\N	ae1e6888-9e5f-4c75-86f9-d5c4386f4d4d
\.


--
-- Data for Name: purchaseorder; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."purchaseorder" ("id", "supplier_id", "status", "created_by", "pdf_url", "created_at", "updated_at") FROM stdin;
\.


--
-- Data for Name: purchaseorderitem; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."purchaseorderitem" ("id", "po_id", "product_id", "quantity", "unit_cost") FROM stdin;
\.


--
-- Data for Name: sale; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."sale" ("id", "product_id", "quantity", "sale_date", "notes", "user_id") FROM stdin;
fd066eb3-939c-447c-a8fb-4e29886d11ce	5555f7a4-20eb-4c66-963f-c2ed91cac445	1	2025-05-06 20:19:51.30504	\N	ec3a64e4-08e2-41e5-9b3a-16cdb5dfaeb0
\.


--
-- Data for Name: skualias; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."skualias" ("id", "alias_sku", "canonical_sku", "notes", "created_at", "user_id") FROM stdin;
\.


--
-- Data for Name: supplier; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."supplier" ("id", "name", "contact_email", "phone", "lead_time_days", "notes", "created_at", "user_id") FROM stdin;
04f57042-3a0a-480e-9870-ee0e5381e8e3	Dam. K	damk@gmail.com	\N	7	\N	2025-05-06 20:09:30.239112	f2111b2d-b47a-4fa2-ab4c-66b4f0bec6da
e4335092-4629-4831-8f27-2652de9961a4	Rohan. S	rohans@gmail.com	\N	7	\N	2025-05-06 20:11:00.832193	f2111b2d-b47a-4fa2-ab4c-66b4f0bec6da
5fd0dc55-42e3-4bae-b193-f082f97ea505	Damodar Kamani	dam_k@gmail.com	\N	7	\N	2025-05-06 20:15:41.508123	ec3a64e4-08e2-41e5-9b3a-16cdb5dfaeb0
5819d228-c3b6-467c-97e5-dd8969edb4db	Dam. K	damk@gmail.com	\N	7	\N	2025-05-06 22:38:57.426394	c13a7b3a-2c84-4e11-8040-e8b5d9c1ec65
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY "public"."user" ("id", "email", "password_hash", "role", "created_at") FROM stdin;
01fe9d0f-7ff5-4eac-98d9-ee0a2a683b0a	test@test.com	$2b$12$eb8TNS17FE5btP1tJh2C9.th/vpxfCLZcsf88FxxpfgdJ4Ahyiz1i	STAFF	2025-05-02 00:23:08.094273
29a3ebaf-0757-4b57-a846-bc6a353503c1	testing@test.com	$2b$12$6eTAlcbCSMQVWfc/hPAlsuZzpn1RUcFXBO9jS73xWzY0h6wqoEuqK	MANAGER	2025-05-03 03:06:47.929449
b67c884b-33eb-453a-ba7f-05c7e73e2fda	testingme@test.com	$2b$12$nzY5OFiVwpmCdNhNvtFvButZlzhCWsc3KzbLLA5DCPCllo3vixJqW	STAFF	2025-05-03 16:08:00.333871
e1c6780f-b789-4a2e-9985-b757ddba80e0	arjan.suri17@gmail.com	$2b$12$isXyOu0HhBEXHCXrL858veh4pTFk.GLQ6TgBBwx0as7r..WKzCSbS	STAFF	2025-05-03 17:07:07.280151
34867284-16ac-4fa9-93bf-0f1cf8cba72b	arjan.suri17@gmail.coms	$2b$12$8PuLRDROQRjeFswOXVh43.8FojP62w1n0LOepitIQBY48O/Z27aUy	STAFF	2025-05-05 05:36:43.46496
69002c11-07e0-4e66-ab2d-82f41103b1c2	a@.com	$2b$12$PaAOG8QpsfY.lPFBdK9GlecVtErT73.d61/2/yYAsDJPLG3kgBZcG	OWNER	2025-05-05 05:46:41.536778
6d88998b-259e-4f8e-bd8b-fb054493bf96	ar@a.c	$2b$12$KalgAlwVUFh6fiXIhrEjxOJ2s8qIH4lY9IEK6GlfiuiFgqRmWpVhy	OWNER	2025-05-05 06:35:29.290432
7331a9bf-1ffb-48ff-864b-e6ddb60a2cef	a@po.com	$2b$12$1TtLgpMp3xFaNv7LqI9TEuC3Zyok9bGFE1.7RJYlE6UqUruHKeT8u	OWNER	2025-05-05 06:40:34.812645
dfaee596-e9d2-4a7b-9db3-84c75378c5ed	arjan@gmail.com	$2b$12$EFdC7E//2BWaM68FUqN9JuJZHbKSN12VKxOycL1UMRe2ultMfz7/a	OWNER	2025-05-05 21:12:30.682117
34a6c53f-ce51-4404-9e2a-90927ce77af6	test@example.com	$2b$12$fMClmJPEhIlVTFmMxz7qNe.YSnyg6JMXfrTcl23zPvIuj7TPPxCSe	OWNER	2025-05-05 21:20:05.99144
0c8bb191-e6f3-4199-ad8c-9d2100869688	test2@example.com	$2b$12$vRcKKAjY6luYQrkUetaiTOsIvVzwhx4vR5K64tNKalCei7WjpOEVq	OWNER	2025-05-06 02:57:18.023128
e02158e3-42bc-4091-a493-06d1d6097498	arjan.s@am.c	$2b$12$gBGL2Oqa/o3l3ZSayghfWO8O3xRBjKexlMLWWK8Ky9ZR3RbiLJ40q	OWNER	2025-05-06 03:11:46.869588
45b54497-4976-4929-966e-52483c01d183	arja@.c	$2b$12$MIqK9nL4oEwLa8hgUgLvQ.67JKmN2X5ureR026Zwj1nIiorUoiDCe	OWNER	2025-05-06 19:04:03.73303
d50ad496-9aee-4b37-b8df-494b3dc81739	arjan@.coma	$2b$12$VpFOOhOK8AEe3tFkH6/sU.ahFuIWdRIynomf7V.SL3MMnDc6vKE92	OWNER	2025-05-06 19:54:51.497383
f2111b2d-b47a-4fa2-ab4c-66b4f0bec6da	arjanm@.coma	$2b$12$JDg64D1c3eO3JGE8IVN6ceulVoejyE5IX3Atlgq4ZI1Tq6KZu7tV.	OWNER	2025-05-06 20:06:34.492574
ec3a64e4-08e2-41e5-9b3a-16cdb5dfaeb0	rohan_sanghavi@gmail.com	$2b$12$ry3.0YGGNxi0jOyuwW.Tm.LiQCpm1Ij7gvpF.bWAd40ScAtRfmCjm	OWNER	2025-05-06 20:14:33.265166
2a0f11a2-71b2-46da-8a2c-176dc86ef053	rohan@enrichify.org	$2b$12$6wVpcWo6Z/oQdKSXelm1T.PbGOZS/08zqPYDOJhcEZyp5ftBnnto2	OWNER	2025-05-06 21:03:18.65596
c13a7b3a-2c84-4e11-8040-e8b5d9c1ec65	arjan.suri1@gmail.com	$2b$12$RJTCfmCq8dSFVqXoQ7jAWO35MVtDnrmJ2E.eRi03uB3dRAEO7Jm5.	OWNER	2025-05-06 22:37:10.543089
ae1e6888-9e5f-4c75-86f9-d5c4386f4d4d	testme@mail.com	$2b$12$0l1rZ7QX4gj5c4yniG6ceeIm2ru91Zyvz9A1TV2cNNemLF64Cr2L.	OWNER	2025-05-06 23:57:15.687808
\.


--
-- Name: connector connector_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."connector"
    ADD CONSTRAINT "connector_pkey" PRIMARY KEY ("id");


--
-- Name: inventoryledger inventoryledger_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."inventoryledger"
    ADD CONSTRAINT "inventoryledger_pkey" PRIMARY KEY ("id");


--
-- Name: notification notification_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."notification"
    ADD CONSTRAINT "notification_pkey" PRIMARY KEY ("id");


--
-- Name: product product_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."product"
    ADD CONSTRAINT "product_pkey" PRIMARY KEY ("id");


--
-- Name: purchaseorder purchaseorder_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."purchaseorder"
    ADD CONSTRAINT "purchaseorder_pkey" PRIMARY KEY ("id");


--
-- Name: purchaseorderitem purchaseorderitem_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."purchaseorderitem"
    ADD CONSTRAINT "purchaseorderitem_pkey" PRIMARY KEY ("id");


--
-- Name: sale sale_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."sale"
    ADD CONSTRAINT "sale_pkey" PRIMARY KEY ("id");


--
-- Name: skualias skualias_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."skualias"
    ADD CONSTRAINT "skualias_pkey" PRIMARY KEY ("id");


--
-- Name: supplier supplier_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."supplier"
    ADD CONSTRAINT "supplier_pkey" PRIMARY KEY ("id");


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."user"
    ADD CONSTRAINT "user_pkey" PRIMARY KEY ("id");


--
-- Name: ix_inventoryledger_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_inventoryledger_source" ON "public"."inventoryledger" USING "btree" ("source");


--
-- Name: ix_product_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_product_name" ON "public"."product" USING "btree" ("name");


--
-- Name: ix_product_sku; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_product_sku" ON "public"."product" USING "btree" ("sku");


--
-- Name: ix_purchaseorder_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_purchaseorder_status" ON "public"."purchaseorder" USING "btree" ("status");


--
-- Name: ix_purchaseorder_supplier_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_purchaseorder_supplier_id" ON "public"."purchaseorder" USING "btree" ("supplier_id");


--
-- Name: ix_skualias_alias_sku; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_skualias_alias_sku" ON "public"."skualias" USING "btree" ("alias_sku");


--
-- Name: ix_supplier_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_supplier_name" ON "public"."supplier" USING "btree" ("name");


--
-- Name: ix_user_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_user_email" ON "public"."user" USING "btree" ("email");


--
-- Name: connector connector_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."connector"
    ADD CONSTRAINT "connector_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."user"("id");


--
-- Name: inventoryledger inventoryledger_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."inventoryledger"
    ADD CONSTRAINT "inventoryledger_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product"("id");


--
-- Name: notification notification_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."notification"
    ADD CONSTRAINT "notification_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id");


--
-- Name: product product_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."product"
    ADD CONSTRAINT "product_supplier_id_fkey" FOREIGN KEY ("supplier_id") REFERENCES "public"."supplier"("id");


--
-- Name: product product_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."product"
    ADD CONSTRAINT "product_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id");


--
-- Name: purchaseorder purchaseorder_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."purchaseorder"
    ADD CONSTRAINT "purchaseorder_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."user"("id");


--
-- Name: purchaseorder purchaseorder_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."purchaseorder"
    ADD CONSTRAINT "purchaseorder_supplier_id_fkey" FOREIGN KEY ("supplier_id") REFERENCES "public"."supplier"("id");


--
-- Name: purchaseorderitem purchaseorderitem_po_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."purchaseorderitem"
    ADD CONSTRAINT "purchaseorderitem_po_id_fkey" FOREIGN KEY ("po_id") REFERENCES "public"."purchaseorder"("id");


--
-- Name: purchaseorderitem purchaseorderitem_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."purchaseorderitem"
    ADD CONSTRAINT "purchaseorderitem_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product"("id");


--
-- Name: sale sale_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."sale"
    ADD CONSTRAINT "sale_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product"("id");


--
-- Name: sale sale_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."sale"
    ADD CONSTRAINT "sale_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id");


--
-- Name: skualias skualias_canonical_sku_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."skualias"
    ADD CONSTRAINT "skualias_canonical_sku_fkey" FOREIGN KEY ("canonical_sku") REFERENCES "public"."product"("sku");


--
-- Name: skualias skualias_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."skualias"
    ADD CONSTRAINT "skualias_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id");


--
-- Name: supplier supplier_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "public"."supplier"
    ADD CONSTRAINT "supplier_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id");


--
-- PostgreSQL database dump complete
--



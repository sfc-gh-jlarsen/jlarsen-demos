--------------------------------------------------------------------
-- BRONZE LAYER: SAP ERP + Salesforce CRM Raw Source Data
-- Run this script to populate sample data for the Power User Skill demo
--------------------------------------------------------------------
USE DATABASE POWER_USER_SKILL_DEMO;
USE SCHEMA BRONZE;

--------------------------------------------------------------------
-- SAP Tables
--------------------------------------------------------------------

CREATE OR REPLACE TABLE SAP_KNA1 (
    KUNNR   VARCHAR(10),
    NAME1   VARCHAR(100),
    NAME2   VARCHAR(100),
    LAND1   VARCHAR(3),
    ORT01   VARCHAR(40),
    STRAS   VARCHAR(60),
    PSTLZ   VARCHAR(10),
    BRSCH   VARCHAR(4),
    KTOKD   VARCHAR(4)
);

INSERT INTO SAP_KNA1 VALUES
    ('0000001000', 'Apex Manufacturing Inc', NULL, 'US', 'Detroit', '100 Industrial Blvd', '48201', 'MACH', 'ZDOM'),
    ('0000001001', 'Northern Steel Corp', NULL, 'CA', 'Toronto', '55 Bay St', 'M5J2T7', 'META', 'ZDOM'),
    ('0000001002', 'Precision Parts GmbH', NULL, 'DE', 'Stuttgart', 'Industriestr 42', '70173', 'MACH', 'ZINT'),
    ('0000001003', 'Global Motors Ltd', NULL, 'GB', 'Birmingham', '1 Auto Way', 'B11AA', 'AUTO', 'ZINT'),
    ('0000001004', 'Pacific Components Co', NULL, 'JP', 'Osaka', '3-1 Umeda', '530001', 'ELEC', 'ZINT'),
    ('0000001005', 'MidWest Fabrication LLC', NULL, 'US', 'Chicago', '200 Steel Ave', '60601', 'META', 'ZDOM'),
    ('0000001006', 'Atlas Engineering SA', 'Div. Automotive', 'FR', 'Lyon', '8 Rue de Industrie', '69001', 'AUTO', 'ZINT'),
    ('0000001007', 'Summit Materials Inc', NULL, 'US', 'Denver', '450 Mountain Rd', '80202', 'CHEM', 'ZDOM'),
    ('0000001008', 'TechPro Solutions Pty', NULL, 'AU', 'Sydney', '12 Harbour St', '2000', 'TECH', 'ZINT'),
    ('0000001009', 'Rio Industrial SA', NULL, 'BR', 'Sao Paulo', 'Av Paulista 1000', '01310', 'MACH', 'ZINT');

CREATE OR REPLACE TABLE SAP_T005T (
    SPRAS VARCHAR(1),
    LAND1 VARCHAR(3),
    LANDX VARCHAR(50)
);

INSERT INTO SAP_T005T VALUES
    ('E', 'US', 'United States'),
    ('E', 'CA', 'Canada'),
    ('E', 'DE', 'Germany'),
    ('E', 'GB', 'United Kingdom'),
    ('E', 'JP', 'Japan'),
    ('E', 'FR', 'France'),
    ('E', 'AU', 'Australia'),
    ('E', 'BR', 'Brazil'),
    ('E', 'CN', 'China'),
    ('E', 'MX', 'Mexico');

CREATE OR REPLACE TABLE SAP_T001 (
    BUKRS VARCHAR(4),
    BUTXT VARCHAR(50),
    WAERS VARCHAR(5),
    LAND1 VARCHAR(3)
);

INSERT INTO SAP_T001 VALUES
    ('1000', 'US Operations', 'USD', 'US'),
    ('2000', 'European Operations', 'EUR', 'DE'),
    ('3000', 'Asia Pacific Operations', 'JPY', 'JP'),
    ('4000', 'Americas South Operations', 'BRL', 'BR');

CREATE OR REPLACE TABLE SAP_MARA (
    MATNR VARCHAR(18),
    MAKTX VARCHAR(80),
    MTART VARCHAR(4),
    MATKL VARCHAR(9),
    MEINS VARCHAR(3),
    BRGEW NUMBER(13,3),
    GEWEI VARCHAR(3)
);

INSERT INTO SAP_MARA VALUES
    ('000000000000100001', 'Hydraulic Cylinder Assembly HCA-200', 'FERT', 'HYDRL', 'EA', 12.500, 'KG'),
    ('000000000000100002', 'Precision Ball Bearing PBB-50', 'FERT', 'BEARNG', 'EA', 0.250, 'KG'),
    ('000000000000100003', 'Stainless Steel Plate 304 2mm', 'ROH', 'STEEL', 'KG', 1.000, 'KG'),
    ('000000000000100004', 'Electric Motor EM-1500 3HP', 'FERT', 'MOTOR', 'EA', 25.000, 'KG'),
    ('000000000000100005', 'Carbon Fiber Sheet CF-10', 'ROH', 'COMPS', 'M2', 0.800, 'KG'),
    ('000000000000100006', 'Pneumatic Valve PV-300', 'FERT', 'VALVE', 'EA', 3.200, 'KG'),
    ('000000000000100007', 'Industrial Gearbox IG-500', 'FERT', 'GEARB', 'EA', 45.000, 'KG'),
    ('000000000000100008', 'Titanium Rod TR-25mm', 'ROH', 'TITAN', 'M', 2.100, 'KG');

CREATE OR REPLACE TABLE SAP_VBAK (
    VBELN   VARCHAR(10),
    ERDAT   DATE,
    KUNNR   VARCHAR(10),
    VKORG   VARCHAR(4),
    WAERK   VARCHAR(5),
    NETWR   NUMBER(15,2),
    AUART   VARCHAR(4),
    BUKRS   VARCHAR(4)
);

INSERT INTO SAP_VBAK VALUES
    ('0050000100', '2025-11-15', '0000001000', '1000', 'USD', 125000.00, 'ZOR', '1000'),
    ('0050000101', '2025-12-01', '0000001001', '1000', 'USD', 87500.00, 'ZOR', '1000'),
    ('0050000102', '2026-01-10', '0000001002', '2000', 'EUR', 210000.00, 'ZOR', '2000'),
    ('0050000103', '2026-01-22', '0000001003', '2000', 'EUR', 55000.00, 'ZOR', '2000'),
    ('0050000104', '2026-02-05', '0000001004', '3000', 'JPY', 15000000.00, 'ZOR', '3000'),
    ('0050000105', '2026-02-18', '0000001000', '1000', 'USD', 340000.00, 'ZOR', '1000'),
    ('0050000106', '2026-03-01', '0000001005', '1000', 'USD', 92000.00, 'ZOR', '1000'),
    ('0050000107', '2026-03-10', '0000001006', '2000', 'EUR', 178000.00, 'ZOR', '2000'),
    ('0050000108', '2026-03-25', '0000001007', '1000', 'USD', 64500.00, 'ZOR', '1000'),
    ('0050000109', '2026-04-01', '0000001002', '2000', 'EUR', 295000.00, 'ZOR', '2000'),
    ('0050000110', '2026-04-10', '0000001008', '3000', 'USD', 115000.00, 'ZOR', '3000'),
    ('0050000111', '2026-04-15', '0000001009', '4000', 'BRL', 450000.00, 'ZOR', '4000');

CREATE OR REPLACE TABLE SAP_VBAP (
    VBELN   VARCHAR(10),
    POSNR   VARCHAR(6),
    MATNR   VARCHAR(18),
    KWMENG  NUMBER(13,3),
    NETPR   NUMBER(11,2),
    WAERK   VARCHAR(5),
    WERKS   VARCHAR(4),
    LGORT   VARCHAR(4)
);

INSERT INTO SAP_VBAP VALUES
    ('0050000100', '000010', '000000000000100001', 50.000, 1500.00, 'USD', '1000', '0001'),
    ('0050000100', '000020', '000000000000100002', 500.000, 25.00, 'USD', '1000', '0001'),
    ('0050000100', '000030', '000000000000100004', 20.000, 2750.00, 'USD', '1000', '0001'),
    ('0050000101', '000010', '000000000000100003', 5000.000, 12.50, 'USD', '1000', '0002'),
    ('0050000101', '000020', '000000000000100006', 100.000, 250.00, 'USD', '1000', '0002'),
    ('0050000102', '000010', '000000000000100007', 30.000, 5500.00, 'EUR', '2000', '0001'),
    ('0050000102', '000020', '000000000000100001', 80.000, 1350.00, 'EUR', '2000', '0001'),
    ('0050000103', '000010', '000000000000100002', 1000.000, 22.00, 'EUR', '2000', '0002'),
    ('0050000103', '000020', '000000000000100005', 200.000, 155.00, 'EUR', '2000', '0002'),
    ('0050000104', '000010', '000000000000100004', 100.000, 120000.00, 'JPY', '3000', '0001'),
    ('0050000104', '000020', '000000000000100008', 500.000, 6000.00, 'JPY', '3000', '0001'),
    ('0050000105', '000010', '000000000000100007', 40.000, 6200.00, 'USD', '1000', '0001'),
    ('0050000105', '000020', '000000000000100001', 100.000, 920.00, 'USD', '1000', '0001'),
    ('0050000106', '000010', '000000000000100003', 4000.000, 13.00, 'USD', '1000', '0003'),
    ('0050000106', '000020', '000000000000100006', 150.000, 260.00, 'USD', '1000', '0003'),
    ('0050000107', '000010', '000000000000100004', 50.000, 2800.00, 'EUR', '2000', '0001'),
    ('0050000107', '000020', '000000000000100002', 2000.000, 19.00, 'EUR', '2000', '0001'),
    ('0050000108', '000010', '000000000000100005', 300.000, 145.00, 'USD', '1000', '0002'),
    ('0050000108', '000020', '000000000000100008', 150.000, 85.00, 'USD', '1000', '0002'),
    ('0050000109', '000010', '000000000000100007', 35.000, 5800.00, 'EUR', '2000', '0001'),
    ('0050000109', '000020', '000000000000100001', 60.000, 1400.00, 'EUR', '2000', '0001'),
    ('0050000110', '000010', '000000000000100004', 30.000, 2900.00, 'USD', '3000', '0001'),
    ('0050000110', '000020', '000000000000100006', 200.000, 240.00, 'USD', '3000', '0001'),
    ('0050000111', '000010', '000000000000100003', 8000.000, 35.00, 'BRL', '4000', '0001'),
    ('0050000111', '000020', '000000000000100002', 3000.000, 50.00, 'BRL', '4000', '0001');

--------------------------------------------------------------------
-- Salesforce Tables
--------------------------------------------------------------------

CREATE OR REPLACE TABLE SFDC_ACCOUNT (
    ID                  VARCHAR(18),
    NAME                VARCHAR(255),
    SAP_ACCOUNT_ID__C   VARCHAR(10),
    INDUSTRY            VARCHAR(100),
    BILLINGCOUNTRY      VARCHAR(80),
    ANNUAL_REVENUE      NUMBER(18,2),
    OWNER_NAME          VARCHAR(100),
    CREATED_DATE        DATE
);

INSERT INTO SFDC_ACCOUNT VALUES
    ('001Abc000001AAaBC', 'Apex Manufacturing Inc', '0000001000', 'Manufacturing', 'United States', 15000000.00, 'Sarah Johnson', '2023-03-15'),
    ('001Abc000001AAaCD', 'Northern Steel Corporation', '0000001001', 'Metals & Mining', 'Canada', 8500000.00, 'Mike Chen', '2023-06-20'),
    ('001Abc000001AAaDE', 'Precision Parts GmbH', '0000001002', 'Manufacturing', 'Germany', 22000000.00, 'Hans Mueller', '2023-01-10'),
    ('001Abc000001AAaEF', 'Global Motors Ltd', '0000001003', 'Automotive', 'United Kingdom', 45000000.00, 'James Wright', '2022-11-05'),
    ('001Abc000001AAaFG', 'Pacific Components Co', '0000001004', 'Electronics', 'Japan', 12000000.00, 'Yuki Tanaka', '2024-02-14'),
    ('001Abc000001AAaGH', 'MidWest Fabrication', '0000001005', 'Manufacturing', 'United States', 5200000.00, 'Sarah Johnson', '2024-05-01'),
    ('001Abc000001AAaHI', 'Atlas Engineering SA', '0000001006', 'Automotive', 'France', 18000000.00, 'Pierre Dupont', '2023-09-22'),
    ('001Abc000001AAaIJ', 'Summit Materials Inc', '0000001007', 'Chemicals', 'United States', 3800000.00, 'Lisa Park', '2024-08-10'),
    ('001Abc000001AAaJK', 'TechPro Solutions', '0000001008', 'Technology', 'Australia', 9200000.00, 'David Brown', '2024-01-18'),
    ('001Abc000001AAaKL', 'Rio Industrial SA', '0000001009', 'Manufacturing', 'Brazil', 7600000.00, 'Carlos Silva', '2024-03-30'),
    ('001Abc000001AAaLM', 'Quantum Dynamics Corp', NULL, 'Aerospace', 'United States', 31000000.00, 'Mike Chen', '2025-01-05'),
    ('001Abc000001AAaMN', 'Nordic Precision AB', NULL, 'Manufacturing', 'Sweden', 11000000.00, 'Hans Mueller', '2025-06-12');

CREATE OR REPLACE TABLE SFDC_OPPORTUNITY (
    ID              VARCHAR(18),
    NAME            VARCHAR(255),
    ACCOUNT_ID      VARCHAR(18),
    AMOUNT          NUMBER(18,2),
    STAGE_NAME      VARCHAR(50),
    CLOSE_DATE      DATE,
    TYPE            VARCHAR(50),
    LEAD_SOURCE     VARCHAR(50),
    CREATED_DATE    DATE
);

INSERT INTO SFDC_OPPORTUNITY VALUES
    ('006Abc000001OpaBC', 'Apex - Hydraulic System Upgrade', '001Abc000001AAaBC', 135000.00, 'Closed Won', '2025-12-15', 'Existing Business', 'Referral', '2025-09-01'),
    ('006Abc000001OpaCD', 'Apex - Q1 2026 Parts Order', '001Abc000001AAaBC', 350000.00, 'Closed Won', '2026-03-01', 'Existing Business', 'Direct', '2025-11-15'),
    ('006Abc000001OpaDE', 'Northern Steel - Steel Supply Agreement', '001Abc000001AAaCD', 95000.00, 'Closed Won', '2026-01-10', 'Existing Business', 'Trade Show', '2025-10-05'),
    ('006Abc000001OpaEF', 'Precision Parts - Gearbox Deal', '001Abc000001AAaDE', 220000.00, 'Closed Won', '2026-02-01', 'Existing Business', 'Referral', '2025-12-01'),
    ('006Abc000001OpaFG', 'Precision Parts - 2026 Expansion', '001Abc000001AAaDE', 310000.00, 'Negotiation', '2026-06-30', 'Existing Business', 'Direct', '2026-01-15'),
    ('006Abc000001OpaGH', 'Global Motors - EV Components', '001Abc000001AAaEF', 60000.00, 'Closed Won', '2026-02-15', 'New Business', 'Web', '2025-11-20'),
    ('006Abc000001OpaHI', 'Pacific Components - Motor Supply', '001Abc000001AAaFG', 125000.00, 'Proposal', '2026-07-15', 'New Business', 'Trade Show', '2026-02-01'),
    ('006Abc000001OpaIJ', 'MidWest Fab - Ongoing Supply', '001Abc000001AAaGH', 98000.00, 'Closed Won', '2026-04-01', 'Existing Business', 'Direct', '2026-01-10'),
    ('006Abc000001OpaJK', 'Atlas Engineering - Auto Parts', '001Abc000001AAaHI', 185000.00, 'Closed Won', '2026-04-10', 'Existing Business', 'Referral', '2025-12-20'),
    ('006Abc000001OpaKL', 'Summit Materials - Chemical Supply', '001Abc000001AAaIJ', 72000.00, 'Qualification', '2026-08-30', 'New Business', 'Web', '2026-03-15'),
    ('006Abc000001OpaLM', 'TechPro - International Deal', '001Abc000001AAaJK', 118000.00, 'Closed Won', '2026-04-20', 'New Business', 'Trade Show', '2026-01-25'),
    ('006Abc000001OpaMN', 'Quantum Dynamics - Aerospace Parts', '001Abc000001AAaLM', 520000.00, 'Proposal', '2026-09-15', 'New Business', 'Conference', '2026-03-01');

CREATE OR REPLACE TABLE SFDC_CONTACT (
    ID              VARCHAR(18),
    ACCOUNT_ID      VARCHAR(18),
    FIRST_NAME      VARCHAR(80),
    LAST_NAME       VARCHAR(80),
    EMAIL           VARCHAR(255),
    TITLE           VARCHAR(128),
    PHONE           VARCHAR(40)
);

INSERT INTO SFDC_CONTACT VALUES
    ('003Abc000001CoaBC', '001Abc000001AAaBC', 'Robert', 'Martinez', 'rmartinez@apexmfg.com', 'VP Procurement', '313-555-0100'),
    ('003Abc000001CoaCD', '001Abc000001AAaBC', 'Jennifer', 'Lee', 'jlee@apexmfg.com', 'Supply Chain Manager', '313-555-0101'),
    ('003Abc000001CoaDE', '001Abc000001AAaCD', 'Andrew', 'Thompson', 'athompson@northernsteel.ca', 'Director of Operations', '416-555-0200'),
    ('003Abc000001CoaEF', '001Abc000001AAaDE', 'Klaus', 'Weber', 'kweber@precisionparts.de', 'Head of Purchasing', '+49-711-555-0300'),
    ('003Abc000001CoaFG', '001Abc000001AAaDE', 'Anna', 'Schmidt', 'aschmidt@precisionparts.de', 'Technical Director', '+49-711-555-0301'),
    ('003Abc000001CoaGH', '001Abc000001AAaEF', 'William', 'Clarke', 'wclarke@globalmotors.co.uk', 'Chief Procurement Officer', '+44-121-555-0400'),
    ('003Abc000001CoaHI', '001Abc000001AAaFG', 'Kenji', 'Yamamoto', 'kyamamoto@pacificcomp.jp', 'General Manager', '+81-6-555-0500'),
    ('003Abc000001CoaIJ', '001Abc000001AAaGH', 'Tom', 'Wilson', 'twilson@midwestfab.com', 'Owner', '312-555-0600'),
    ('003Abc000001CoaJK', '001Abc000001AAaHI', 'Marie', 'Lefebvre', 'mlefebvre@atlaseng.fr', 'VP Engineering', '+33-4-555-0700'),
    ('003Abc000001CoaKL', '001Abc000001AAaIJ', 'Rachel', 'Adams', 'radams@summitmat.com', 'Buyer', '303-555-0800'),
    ('003Abc000001CoaLM', '001Abc000001AAaJK', 'Emma', 'Taylor', 'etaylor@techpro.com.au', 'Operations Manager', '+61-2-555-0900'),
    ('003Abc000001CoaMN', '001Abc000001AAaKL', 'Lucas', 'Oliveira', 'loliveira@rioindustrial.br', 'Director', '+55-11-555-1000');

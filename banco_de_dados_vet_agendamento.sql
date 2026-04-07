CREATE DATABASE  IF NOT EXISTS `vet_agendamento` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `vet_agendamento`;
-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: vet_agendamento
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `agendamentos`
--

DROP TABLE IF EXISTS `agendamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agendamentos` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `tutor_id` int unsigned NOT NULL,
  `veterinario_id` int unsigned NOT NULL,
  `pet_id` int unsigned NOT NULL,
  `data_hora` datetime NOT NULL,
  `duracao_min` smallint unsigned NOT NULL DEFAULT '30',
  `status` enum('pendente','confirmado','cancelado','concluido','remarcado') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pendente',
  `motivo_consulta` text COLLATE utf8mb4_unicode_ci,
  `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_ag_vet` (`veterinario_id`),
  KEY `fk_ag_pet` (`pet_id`),
  KEY `idx_ag_tutor` (`tutor_id`),
  CONSTRAINT `fk_ag_pet` FOREIGN KEY (`pet_id`) REFERENCES `pets` (`id`),
  CONSTRAINT `fk_ag_tutor` FOREIGN KEY (`tutor_id`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `fk_ag_vet` FOREIGN KEY (`veterinario_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agendamentos`
--

LOCK TABLES `agendamentos` WRITE;
/*!40000 ALTER TABLE `agendamentos` DISABLE KEYS */;
INSERT INTO `agendamentos` VALUES (1,1,2,1,'2026-04-15 14:00:00',30,'remarcado','Consulta de rotina','2026-04-04 12:22:55','2026-04-04 12:33:44'),(2,1,2,1,'2026-04-20 10:00:00',30,'cancelado','Vacina','2026-04-04 12:34:28','2026-04-04 12:34:36'),(3,1,2,1,'2026-04-15 14:00:00',30,'pendente','Teste de conflito','2026-04-04 12:35:58','2026-04-04 12:35:58'),(4,1,2,1,'2026-05-10 09:00:00',30,'pendente','Consulta A','2026-04-04 12:36:38','2026-04-04 12:36:38');
/*!40000 ALTER TABLE `agendamentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bloqueios_agenda`
--

DROP TABLE IF EXISTS `bloqueios_agenda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bloqueios_agenda` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `veterinario_id` int unsigned NOT NULL,
  `data_inicio` datetime NOT NULL,
  `data_fim` datetime NOT NULL,
  `motivo` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_ba_vet` (`veterinario_id`),
  CONSTRAINT `fk_ba_vet` FOREIGN KEY (`veterinario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bloqueios_agenda`
--

LOCK TABLES `bloqueios_agenda` WRITE;
/*!40000 ALTER TABLE `bloqueios_agenda` DISABLE KEYS */;
INSERT INTO `bloqueios_agenda` VALUES (1,2,'2026-05-20 08:00:00','2026-05-20 18:00:00','Congresso veterinario');
/*!40000 ALTER TABLE `bloqueios_agenda` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historico_atendimentos`
--

DROP TABLE IF EXISTS `historico_atendimentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historico_atendimentos` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `agendamento_id` int unsigned NOT NULL,
  `diagnostico` text COLLATE utf8mb4_unicode_ci,
  `prescricao` text COLLATE utf8mb4_unicode_ci,
  `observacoes` text COLLATE utf8mb4_unicode_ci,
  `peso_kg` decimal(5,2) DEFAULT NULL,
  `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `agendamento_id` (`agendamento_id`),
  CONSTRAINT `fk_ha_ag` FOREIGN KEY (`agendamento_id`) REFERENCES `agendamentos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historico_atendimentos`
--

LOCK TABLES `historico_atendimentos` WRITE;
/*!40000 ALTER TABLE `historico_atendimentos` DISABLE KEYS */;
INSERT INTO `historico_atendimentos` VALUES (1,1,'Animal saudavel','Nenhuma','Retorno em 6 meses',12.50,'2026-04-04 12:26:50');
/*!40000 ALTER TABLE `historico_atendimentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `horarios_padrao`
--

DROP TABLE IF EXISTS `horarios_padrao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `horarios_padrao` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `veterinario_id` int unsigned NOT NULL,
  `dia_semana` tinyint unsigned NOT NULL,
  `hora_inicio` time NOT NULL,
  `hora_fim` time NOT NULL,
  `duracao_consulta_min` smallint unsigned NOT NULL DEFAULT '30',
  PRIMARY KEY (`id`),
  KEY `fk_hp_vet` (`veterinario_id`),
  CONSTRAINT `fk_hp_vet` FOREIGN KEY (`veterinario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `horarios_padrao`
--

LOCK TABLES `horarios_padrao` WRITE;
/*!40000 ALTER TABLE `horarios_padrao` DISABLE KEYS */;
/*!40000 ALTER TABLE `horarios_padrao` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pets`
--

DROP TABLE IF EXISTS `pets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pets` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `tutor_id` int unsigned NOT NULL,
  `nome` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `especie` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `raca` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `data_nasc` date DEFAULT NULL,
  `sexo` enum('M','F','desconhecido') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'desconhecido',
  `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_pet_tutor` (`tutor_id`),
  CONSTRAINT `fk_pet_tutor` FOREIGN KEY (`tutor_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pets`
--

LOCK TABLES `pets` WRITE;
/*!40000 ALTER TABLE `pets` DISABLE KEYS */;
INSERT INTO `pets` VALUES (1,1,'Rex','cao','Labrador',NULL,'M','2026-04-04 12:18:23');
/*!40000 ALTER TABLE `pets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `nome` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `senha_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `perfil` enum('tutor','veterinario') COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'Teste','teste@email.com','$2b$12$RtmC3J6JYk3twDkjgMbzOO71OteQj2JjnRmSNufAA7wHQCdGlhlE.','tutor',NULL,'2026-04-04 12:06:24','2026-04-04 12:06:24'),(2,'Dra. Ana','ana@vet.com','$2b$12$haczCONNqlINSc/VA5Inu.gVVz/Qk2e2ajQeoR42Yl9SqUnoLa48S','veterinario',NULL,'2026-04-04 12:22:41','2026-04-04 12:22:41');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-06 10:24:43

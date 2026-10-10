CREATE TABLE `alerts` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`listing_id` text NOT NULL,
	`target` integer NOT NULL,
	`enabled` integer DEFAULT 1 NOT NULL,
	`triggered_at` text,
	`created_at` text NOT NULL,
	FOREIGN KEY (`listing_id`) REFERENCES `listings`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `decisions` (
	`id` text PRIMARY KEY NOT NULL,
	`listing_a` text NOT NULL,
	`listing_b` text NOT NULL,
	`decision` text NOT NULL,
	`score` integer NOT NULL,
	`reason` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `decision_pair` ON `decisions` (`listing_a`,`listing_b`);--> statement-breakpoint
CREATE TABLE `discounts` (
	`id` text PRIMARY KEY NOT NULL,
	`observation_id` text NOT NULL,
	`type` text NOT NULL,
	`details` text NOT NULL,
	`verified` integer DEFAULT 0 NOT NULL,
	FOREIGN KEY (`observation_id`) REFERENCES `observations`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `errors` (
	`id` text PRIMARY KEY NOT NULL,
	`platform` text NOT NULL,
	`listing_id` text,
	`code` text NOT NULL,
	`message` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `errors_platform_time` ON `errors` (`platform`,`created_at`);--> statement-breakpoint
CREATE TABLE `jobs` (
	`id` text PRIMARY KEY NOT NULL,
	`listing_id` text NOT NULL,
	`due_at` text NOT NULL,
	`interval` integer DEFAULT 21600 NOT NULL,
	`attempt` integer DEFAULT 0 NOT NULL,
	`state` text DEFAULT 'pending' NOT NULL,
	`lease_until` text,
	`last_error` text,
	FOREIGN KEY (`listing_id`) REFERENCES `listings`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `job_listing` ON `jobs` (`listing_id`);--> statement-breakpoint
CREATE INDEX `jobs_due` ON `jobs` (`state`,`due_at`);--> statement-breakpoint
CREATE TABLE `listings` (
	`id` text PRIMARY KEY NOT NULL,
	`product_id` text NOT NULL,
	`variant_id` text NOT NULL,
	`platform` text NOT NULL,
	`seller_id` text,
	`url` text NOT NULL,
	`title` text NOT NULL,
	`price` integer,
	`mrp` integer,
	`shipping` integer,
	`availability` text DEFAULT 'Unknown' NOT NULL,
	`last_verified` text,
	`state` text DEFAULT 'stale' NOT NULL,
	`evidence` text,
	`created_at` text NOT NULL,
	FOREIGN KEY (`product_id`) REFERENCES `products`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`variant_id`) REFERENCES `variants`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`platform`) REFERENCES `platforms`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`seller_id`) REFERENCES `sellers`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `listing_url` ON `listings` (`url`);--> statement-breakpoint
CREATE INDEX `listing_product` ON `listings` (`product_id`);--> statement-breakpoint
CREATE INDEX `listing_platform` ON `listings` (`platform`);--> statement-breakpoint
CREATE TABLE `notifications` (
	`id` text PRIMARY KEY NOT NULL,
	`alert_id` text,
	`user_id` text NOT NULL,
	`listing_id` text NOT NULL,
	`message` text NOT NULL,
	`created_at` text NOT NULL,
	`read` integer DEFAULT 0 NOT NULL,
	FOREIGN KEY (`alert_id`) REFERENCES `alerts`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `observations` (
	`id` text PRIMARY KEY NOT NULL,
	`product_id` text NOT NULL,
	`listing_id` text NOT NULL,
	`platform` text NOT NULL,
	`price` integer NOT NULL,
	`observed_at` text NOT NULL,
	`seller` text,
	`availability` text NOT NULL,
	`verification` text NOT NULL,
	`discount_details` text DEFAULT '[]' NOT NULL,
	`run_id` text NOT NULL,
	FOREIGN KEY (`product_id`) REFERENCES `products`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`listing_id`) REFERENCES `listings`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `observation_run` ON `observations` (`listing_id`,`run_id`);--> statement-breakpoint
CREATE INDEX `history_listing_time` ON `observations` (`listing_id`,`observed_at`);--> statement-breakpoint
CREATE INDEX `history_product_time` ON `observations` (`product_id`,`observed_at`);--> statement-breakpoint
CREATE TABLE `platforms` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`host` text NOT NULL,
	`status` text DEFAULT 'untested' NOT NULL,
	`last_success` text,
	`last_error` text,
	`paused_until` text
);
--> statement-breakpoint
CREATE TABLE `products` (
	`id` text PRIMARY KEY NOT NULL,
	`title` text NOT NULL,
	`brand` text,
	`model` text,
	`gtin` text,
	`category` text DEFAULT 'Other' NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `sellers` (
	`id` text PRIMARY KEY NOT NULL,
	`platform` text NOT NULL,
	`name` text NOT NULL,
	FOREIGN KEY (`platform`) REFERENCES `platforms`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `seller_name` ON `sellers` (`platform`,`name`);--> statement-breakpoint
CREATE TABLE `settings` (
	`user_id` text PRIMARY KEY NOT NULL,
	`interval` integer DEFAULT 21600 NOT NULL,
	`notifications` integer DEFAULT 1 NOT NULL
);
--> statement-breakpoint
CREATE TABLE `variants` (
	`id` text PRIMARY KEY NOT NULL,
	`product_id` text NOT NULL,
	`attributes` text NOT NULL,
	FOREIGN KEY (`product_id`) REFERENCES `products`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `variants_product` ON `variants` (`product_id`);--> statement-breakpoint
CREATE TABLE `watchlists` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`listing_id` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`listing_id`) REFERENCES `listings`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `watch_user_listing` ON `watchlists` (`user_id`,`listing_id`);
# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json, hub
from frappe.website.website_generator import WebsiteGenerator
from hub.hub.utils import autoname_increment_by_field
from frappe.utils.file_manager import save_file

MAX_SELLER_ITEM_COUNT = 200

class HubItem(WebsiteGenerator):
	website = frappe._dict(
		page_title_field = "item_name"
	)

	def autoname(self):
		name_length = 16
		hash_length = 12
		super(HubItem, self).autoname()
		self.name = self.name[:name_length] + '-' + frappe.generate_hash(self.doctype, hash_length)

	def validate(self):
		seller_item_count = frappe.db.count("Hub Item", {"hub_seller": self.hub_seller})

		if seller_item_count >= MAX_SELLER_ITEM_COUNT:
			frappe.throw('Max allowed items for seller {seller} exceeded.'.format(seller=self.hub_seller))

		if not self.route:
			self.route = 'items/' + self.name

		self.update_keywords_field()
		self.extract_image_from_base64()

	def update_keywords_field(self):
		# update fulltext field
		keyword_fields = ["name", "item_name", "item_code", "hub_category",
			"hub_seller.company", "hub_seller.country", "hub_seller.company_description"]

		keywords = []

		for field in keyword_fields:
			if '.' in field:
				link_field, fieldname = field.split(".")
				doctype = self.meta.get_field(link_field).options
				name = self.get(link_field)
				value = frappe.db.get_value(doctype, name, fieldname)

				keywords.append(value or "")

			else:
				keywords.append(self.get(field, "") or "")

		self.keywords = (" ").join(keywords)

	def extract_image_from_base64(self):
		if self.image and self.image.startswith('{'):
			self.image = json.loads(self.image)

			image_file_name = self.image['file_name']
			base64 = self.image['base64']

			if image_file_name and base64 and not is_valid_file_url(base64):
				f = save_file(image_file_name, base64, self.doctype, self.name, decode=True)
				self.image = f.file_url

	def get_context(self, context):
		context.no_cache = True

def get_list_context(context):
	context.allow_guest = True
	context.no_cache = True
	context.title = 'Items'
	context.no_breadcrumbs = True
	context.order_by = 'creation desc'

def is_valid_file_url(file_url):
	'''Check if url is a valid relative url or absolute url'''
	return (file_url.startswith('/files')
		or file_url.startswith('/private/files')
		or file_url.startswith('http'))

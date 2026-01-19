import sys
import io
import os
import math
import argparse
from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from reportlab import rl_config
from PIL import Image, ImageSequence
from pypdf import PdfWriter, PdfReader
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntSelligenceClient
from dotenv import load_dotenv
load_dotenv()



class ConvertPdf2SearchableFormat:

    def __init__(self, input_file_path, output_file_path):
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path


    
    @staticmethod
    def _dist(polygon, i1, i2):
        x1, y1 = polygon[i1], polygon[i1 + 1]
        x2, y2 = polygon[i2], polygon[i2 + 1]
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    

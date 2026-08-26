---
question_id: "06878be2"
session_index: 17
session_id: "sharegpt_5cxEGva_147"
timestamp: "2023/05/23 (Tue) 02:43"
is_evidence_session: false
turn_count: 3
translation_status: TODO
---
# Session 017 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
Apologies for the confusion earlier. Here's the complete script using SuiteScript 2.0:
```javascript
/**
 * This script demonstrates how to search for a Sales Order in NetSuite using SuiteScript 2.0.
 */

/**
 * @NApiVersion 2.x
 * @NScriptType Suitelet
 * @NModuleScope SameAccount
 */

define(['N/search', 'N/ui/serverWidget'], function(search, serverWidget) {
  
  function onRequest(context) {
    
    // Create a form
    var form = serverWidget.createForm({
      title: 'Sales Order Search'
    });
    
    // Add a field to enter the Sales Order number
    form.addField({
      id: 'custpage_sales_order_number',
      type: serverWidget.FieldType.TEXT,
      label: 'Sales Order Number'
    });
    
    // Add a submit button to the form
    form.addSubmitButton({
      label: 'Search'
    });
    
    // If the form has been submitted
    if (context.request.method === 'POST') {
      
      // Get the Sales Order number entered by the user
      var salesOrderNumber = context.request.parameters.custpage_sales_order_number;
      
      // Create a Sales Order search
      var salesOrderSearch = search.create({
        type: search.Type.SALES_ORDER,
        filters: [
          ['tranid', 'is', salesOrderNumber]
        ],
        columns: ['internalid', 'tranid', 'entity', 'trandate']
      });
      
      // Run the search and get the search results
      var searchResult = salesOrderSearch.run();
      var results = searchResult.getRange({
        start: 0,
        end: 100
      });
      
      // Create a sublist to display the search results
      var sublist = form.addSublist({
        id: 'custpage_sales_order_sublist',
        type: serverWidget.SublistType.LIST,
        label: 'Sales Order Search Results'
      });
      
      // Add columns to the sublist
      sublist.addField({
        id: 'custpage_sales_order_internal_id',
        type: serverWidget.FieldType.TEXT,
        label: 'Internal ID'
      });
      sublist.addField({
        id: 'custpage_sales_order_number',
        type: serverWidget.FieldType.TEXT,
        label: 'Sales Order Number'
      });
      sublist.addField({
        id: 'custpage_sales_order_customer',
        type: serverWidget.FieldType.TEXT,
        label: 'Customer'
      });
      sublist.addField({
        id: 'custpage_sales_order_date',
        type: serverWidget.FieldType.DATE,
        label: 'Date'
      });
      
      // Add the search results to the sublist
      for (var i = 0; i < results.length; i++) {
        var result = results[i];
        sublist.setSublistValue({
          id: 'custpage_sales_order_internal_id',
          line: i,
          value: result.getValue({name: 'internalid'})
        });
        sublist.setSublistValue({
          id: 'custpage_sales_order_number',
          line: i,
          value: result.getValue({name: 'tranid'})
        });
        sublist.setSublistValue({
          id: 'custpage_sales_order_customer',
          line: i,
          value: result.getText({name: 'entity'})
        });
        sublist.setSublistValue({
          id: 'custpage_sales_order_date',
          line: i,
          value: result.getValue({name: 'trandate'})
        });
      }
      
    }
    
    // Display the form
    context.response.writePage(form);
    
  }
  
  return {
    onRequest: onRequest
  };
  
});
```
Note that this script
<!-- SOURCE_TURN_000_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_000_BEGIN -->
对于之前的混淆表示歉意。以下是使用 SuiteScript 2.0 的完整脚本：
```javascript
/**
 * 此脚本演示如何使用 SuiteScript 2.0 在 NetSuite 中搜索销售订单。
 */

/**
 * @NApiVersion 2.x
 * @NScriptType Suitelet
 * @NModuleScope SameAccount
 */

define(['N/search', 'N/ui/serverWidget'], function(search, serverWidget) {
  
  function onRequest(context) {
    
    // 创建表单
    var form = serverWidget.createForm({
      title: '销售订单搜索'
    });
    
    // 添加输入销售订单号的字段
    form.addField({
      id: 'custpage_sales_order_number',
      type: serverWidget.FieldType.TEXT,
      label: '销售订单号'
    });
    
    // 向表单添加提交按钮
    form.addSubmitButton({
      label: '搜索'
    });
    
    // 如果表单已提交
    if (context.request.method === 'POST') {
      
      // 获取用户输入的销售订单号
      var salesOrderNumber = context.request.parameters.custpage_sales_order_number;
      
      // 创建销售订单搜索
      var salesOrderSearch = search.create({
        type: search.Type.SALES_ORDER,
        filters: [
          ['tranid', 'is', salesOrderNumber]
        ],
        columns: ['internalid', 'tranid', 'entity', 'trandate']
      });
      
      // 运行搜索并获取搜索结果
      var searchResult = salesOrderSearch.run();
      var results = searchResult.getRange({
        start: 0,
        end: 100
      });
      
      // 创建子列表以显示搜索结果
      var sublist = form.addSublist({
        id: 'custpage_sales_order_sublist',
        type: serverWidget.SublistType.LIST,
        label: '销售订单搜索结果'
      });
      
      // 向子列表添加列
      sublist.addField({
        id: 'custpage_sales_order_internal_id',
        type: serverWidget.FieldType.TEXT,
        label: '内部 ID'
      });
      sublist.addField({
        id: 'custpage_sales_order_number',
        type: serverWidget.FieldType.TEXT,
        label: '销售订单号'
      });
      sublist.addField({
        id: 'custpage_sales_order_customer',
        type: serverWidget.FieldType.TEXT,
        label: '客户'
      });
      sublist.addField({
        id: 'custpage_sales_order_date',
        type: serverWidget.FieldType.DATE,
        label: '日期'
      });
      
      // 将搜索结果添加到子列表
      for (var i = 0; i < results.length; i++) {
        var result = results[i];
        sublist.setSublistValue({
          id: 'custpage_sales_order_internal_id',
          line: i,
          value: result.getValue({name: 'internalid'})
        });
        sublist.setSublistValue({
          id: 'custpage_sales_order_number',
          line: i,
          value: result.getValue({name: 'tranid'})
        });
        sublist.setSublistValue({
          id: 'custpage_sales_order_customer',
          line: i,
          value: result.getText({name: 'entity'})
        });
        sublist.setSublistValue({
          id: 'custpage_sales_order_date',
          line: i,
          value: result.getValue({name: 'trandate'})
        });
      }
      
    }
    
    // 显示表单
    context.response.writePage(form);
    
  }
  
  return {
    onRequest: onRequest
  };
  
});
```
请注意，此脚本
<!-- ZH_TURN_000_END -->

## Turn 001 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_001_BEGIN -->
that suitelet does not have the pagination I asked for
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
那个 suitelet 没有我要求的分页功能
<!-- ZH_TURN_001_END -->

## Turn 002 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_002_BEGIN -->
I apologize for the confusion earlier. Here is an updated script that includes pagination:
```javascript
/**
 * @NApiVersion 2.x
 * @NScriptType Suitelet
 * @NModuleScope SameAccount
 */
define(['N/ui/serverWidget', 'N/search'], function(ui, search) {

  function onRequest(context) {
    if (context.request.method === 'GET') {
      // create form
      var form = ui.createForm({
        title: 'Sales Order Search'
      });

      // add search field
      var searchField = form.addField({
        id: 'search',
        type: ui.FieldType.TEXT,
        label: 'Search'
      });

      // add submit button
      form.addSubmitButton({
        label: 'Search'
      });

      // add sublist
      var sublist = form.addSublist({
        id: 'results',
        type: ui.SublistType.LIST,
        label: 'Search Results'
      });

      // add columns to sublist
      sublist.addField({
        id: 'salesorder',
        type: ui.FieldType.TEXT,
        label: 'Sales Order'
      });
      sublist.addField({
        id: 'entity',
        type: ui.FieldType.TEXT,
        label: 'Entity'
      });
      sublist.addField({
        id: 'trandate',
        type: ui.FieldType.DATE,
        label: 'Date'
      });
      sublist.addField({
        id: 'amount',
        type: ui.FieldType.CURRENCY,
        label: 'Amount'
      });

      // render form
      context.response.writePage(form);

    } else if (context.request.method === 'POST') {
      // retrieve search query parameter
      var searchQuery = context.request.parameters.search;

      // create search object
      var salesOrderSearch = search.create({
        type: search.Type.SALES_ORDER,
        filters: [
          search.createFilter({
            name: 'mainline',
            operator: search.Operator.IS,
            values: ['T']
          }),
          search.createFilter({
            name: 'status',
            operator: search.Operator.ANYOF,
            values: ['SalesOrd:F']
          }),
          search.createFilter({
            name: 'number',
            operator: search.Operator.CONTAINS,
            values: searchQuery
          })
        ],
        columns: [
          search.createColumn({
            name: 'tranid',
            sort: search.Sort.DESC
          }),
          search.createColumn({
            name: 'entity'
          }),
          search.createColumn({
            name: 'trandate'
          }),
          search.createColumn({
            name: 'amount'
          })
        ]
      });

      // retrieve page parameter
      var currentPage = parseInt(context.request.parameters.page) || 1;
      var pageSize = 10;

      // set the page range
      var startIndex = (currentPage - 1) * pageSize;
      var endIndex = startIndex + pageSize;

      // run search with paged results
      var searchResult = salesOrderSearch.runPaged({
        pageSize: pageSize
      });

      // retrieve the sublist from the form
      var sublist = form.getSublist({
        id: 'results'
      });

      // clear existing sublist items
      sublist.removeLine({
        from: 0,
        to: sublist.getLineCount()
      });

      // iterate over the search results for the current page and add them to the sublist
      searchResult.pageRanges.forEach(function(pageRange) {
        if (pageRange.index >= startIndex && pageRange.index < endIndex) {
          var currentPageResults = searchResult.fetch({
            index: pageRange.index
          });
          currentPageResults.data.forEach(function(result) {
            sublist.setSublistValue({
              id: 'salesorder',
              line: sublist.getLineCount(),
```
<!-- SOURCE_TURN_002_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_002_BEGIN -->
对于之前的混淆表示歉意。以下是包含分页功能的更新脚本：
```javascript
/**
 * @NApiVersion 2.x
 * @NScriptType Suitelet
 * @NModuleScope SameAccount
 */
define(['N/ui/serverWidget', 'N/search'], function(ui, search) {

  function onRequest(context) {
    if (context.request.method === 'GET') {
      // 创建表单
      var form = ui.createForm({
        title: '销售订单搜索'
      });

      // 添加搜索字段
      var searchField = form.addField({
        id: 'search',
        type: ui.FieldType.TEXT,
        label: '搜索'
      });

      // 添加提交按钮
      form.addSubmitButton({
        label: '搜索'
      });

      // 添加子列表
      var sublist = form.addSublist({
        id: 'results',
        type: ui.SublistType.LIST,
        label: '搜索结果'
      });

      // 向子列表添加列
      sublist.addField({
        id: 'salesorder',
        type: ui.FieldType.TEXT,
        label: '销售订单'
      });
      sublist.addField({
        id: 'entity',
        type: ui.FieldType.TEXT,
        label: '实体'
      });
      sublist.addField({
        id: 'trandate',
        type: ui.FieldType.DATE,
        label: '日期'
      });
      sublist.addField({
        id: 'amount',
        type: ui.FieldType.CURRENCY,
        label: '金额'
      });

      // 渲染表单
      context.response.writePage(form);

    } else if (context.request.method === 'POST') {
      // 检索搜索查询参数
      var searchQuery = context.request.parameters.search;

      // 创建搜索对象
      var salesOrderSearch = search.create({
        type: search.Type.SALES_ORDER,
        filters: [
          search.createFilter({
            name: 'mainline',
            operator: search.Operator.IS,
            values: ['T']
          }),
          search.createFilter({
            name: 'status',
            operator: search.Operator.ANYOF,
            values: ['SalesOrd:F']
          }),
          search.createFilter({
            name: 'number',
            operator: search.Operator.CONTAINS,
            values: searchQuery
          })
        ],
        columns: [
          search.createColumn({
            name: 'tranid',
            sort: search.Sort.DESC
          }),
          search.createColumn({
            name: 'entity'
          }),
          search.createColumn({
            name: 'trandate'
          }),
          search.createColumn({
            name: 'amount'
          })
        ]
      });

      // 检索页码参数
      var currentPage = parseInt(context.request.parameters.page) || 1;
      var pageSize = 10;

      // 设置页面范围
      var startIndex = (currentPage - 1) * pageSize;
      var endIndex = startIndex + pageSize;

      // 使用分页结果运行搜索
      var searchResult = salesOrderSearch.runPaged({
        pageSize: pageSize
      });

      // 从表单中检索子列表
      var sublist = form.getSublist({
        id: 'results'
      });

      // 清除现有的子列表项
      sublist.removeLine({
        from: 0,
        to: sublist.getLineCount()
      });

      // 遍历当前页的搜索结果并将其添加到子列表
      searchResult.pageRanges.forEach(function(pageRange) {
        if (pageRange.index >= startIndex && pageRange.index < endIndex) {
          var currentPageResults = searchResult.fetch({
            index: pageRange.index
          });
          currentPageResults.data.forEach(function(result) {
            sublist.setSublistValue({
              id: 'salesorder',
              line: sublist.getLineCount(),
<!-- ZH_TURN_002_END -->

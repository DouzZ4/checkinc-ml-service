# Ejemplo: Integración de Predicciones ML en Check.Inc

Esta página demuestra cómo integrar y mostrar las predicciones de Machine Learning en tu aplicación JSF con PrimeFaces.

## Opción 1: Vista Simple con DataTable

```xhtml
<?xml version='1.0' encoding='UTF-8' ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:h="http://xmlns.jcp.org/jsf/html"
      xmlns:f="http://xmlns.jcp.org/jsf/core"
      xmlns:p="http://primefaces.org/ui">
    
    <h:head>
        <title>Predicciones ML - Check.Inc</title>
    </h:head>
    
    <h:body>
        <h:form id="formPredicciones">
            
            <!-- Panel de Control -->
            <p:panel header="⚙️ Configuración de Predicción">
                <h:panelGrid columns="2" cellpadding="5">
                    <p:outputLabel for="horas" value="Horas a predecir:"/>
                    <p:spinner id="horas" value="#{prediccionMLBean.horasAdelante}" 
                               min="1" max="24" stepFactor="1"/>
                    
                    <p:commandButton value="🔮 Generar Predicciones" 
                                     actionListener="#{prediccionMLBean.cargarPredicciones}"
                                     update="@form" 
                                     styleClass="ui-button-success"/>
                </h:panelGrid>
            </p:panel>
            
            <!-- Tabla de Predicciones -->
            <p:panel header="📊 Predicciones de Glucosa" style="margin-top:20px">
                <p:dataTable value="#{prediccionMLBean.predicciones}" 
                             var="pred"
                             emptyMessage="No hay predicciones disponibles">
                    
                    <p:column headerText="Fecha/Hora">
                        <h:outputText value="#{pred.timestamp}"/>
                    </p:column>
                    
                    <p:column headerText="Nivel Predicho (mg/dL)">
                        <h:outputText value="#{pred.nivelPredicho}" 
                                      style="font-weight:bold; font-size:16px;">
                            <f:convertNumber pattern="#0.0"/>
                        </h:outputText>
                    </p:column>
                    
                    <p:column headerText="Confianza">
                        <p:progressBar value="#{pred.confianza * 100}" 
                                       displayValue="#{pred.confianza * 100}%"
                                       labelTemplate="{value}%"/>
                    </p:column>
                    
                </p:dataTable>
            </p:panel>
            
            <!-- Panel de Evaluación de Riesgo -->
            <p:panel header="⚠️ Evaluación de Riesgo" style="margin-top:20px">
                <p:commandButton value="Evaluar Riesgo Actual" 
                                 actionListener="#{prediccionMLBean.cargarEvaluacionRiesgo}"
                                 update="panelRiesgo"/>
                
                <h:panelGroup id="panelRiesgo" layout="block" style="margin-top:15px">
                    <h:panelGrid columns="2" cellpadding="10" rendered="#{not empty prediccionMLBean.nivelRiesgo}">
                        
                        <h:outputText value="Nivel de Riesgo:"/>
                        <p:badge value="#{prediccionMLBean.nivelRiesgo}" 
                                 severity="#{prediccionMLBean.colorRiesgo}"
                                 size="xlarge"/>
                        
                        <h:outputText value="Puntuación:"/>
                        <h:outputText value="#{prediccionMLBean.riesgoScore * 100}%">
                            <f:convertNumber pattern="#0.0"/>
                        </h:outputText>
                        
                        <h:outputText value="Promedio 7 días:"/>
                        <h:outputText value="#{prediccionMLBean.promedioGlucosa} mg/dL">
                            <f:convertNumber pattern="#0.0"/>
                        </h:outputText>
                        
                        <h:outputText value="Eventos Hipoglucemia:"/>
                        <h:outputText value="#{prediccionMLBean.eventosHipo}" 
                                      style="color:red; font-weight:bold;"/>
                        
                        <h:outputText value="Eventos Hiperglucemia:"/>
                        <h:outputText value="#{prediccionMLBean.eventosHiper}" 
                                      style="color:orange; font-weight:bold;"/>
                    </h:panelGrid>
                </h:panelGroup>
            </p:panel>
            
            <!-- Panel de Recomendaciones -->
            <p:panel header="💡 Recomendaciones Personalizadas" style="margin-top:20px">
                <p:dataList value="#{prediccionMLBean.recomendaciones}" 
                            var="rec"
                            emptyMessage="No hay recomendaciones disponibles">
                    <p:column>
                        <h:outputText value="• #{rec}"/>
                    </p:column>
                </p:dataList>
            </p:panel>
            
            <!-- Mensajes de estado -->
            <p:growl id="messages"/>
            
        </h:form>
    </h:body>
</html>
```

## Opción 2: Vista Avanzada con Gráfico

Si quieres mostrar las predicciones en un gráfico junto con los valores reales, integra con `p:chart`:

```xhtml
<!-- Panel con Gráfico de Predicciones -->
<p:panel header="📈 Gráfico Predictivo">
    <p:chart type="line" model="#{prediccionMLBean.chartModel}" 
             style="width:100%; height:400px"/>
</p:panel>
```

En el bean, crea el modelo del gráfico:

```java
public LineChartModel getChartModel() {
    LineChartModel model = new LineChartModel();
    ChartData data = new ChartData();
    
    // Dataset de predicciones
    LineChartDataSet predDataSet = new LineChartDataSet();
    predDataSet.setLabel("Predicciones");
    predDataSet.setBorderColor("rgb(255, 99, 132)");
    predDataSet.setBorderDash(Arrays.asList(5, 5));
    
    List<Object> predValues = predicciones.stream()
        .map(p -> p.getNivelPredicho())
        .collect(Collectors.toList());
    
    List<String> labels = predicciones.stream()
        .map(p -> p.getTimestamp())
        .collect(Collectors.toList());
    
    predDataSet.setData(predValues);
    data.addChartDataSet(predDataSet);
    data.setLabels(labels);
    
    model.setData(data);
    return model;
}
```

## Navegación

Añade enlace en tu menú principal:

```xhtml
<p:menuitem value="🔮 Predicciones ML" 
            outcome="/views/predicciones-ml.xhtml" 
            icon="pi pi-chart-line"/>
```

## Estilo CSS (Opcional)

```css
.risk-badge-bajo {
    background-color: #38a169;
    color: white;
    padding: 5px 15px;
    border-radius: 20px;
}

.risk-badge-medio {
    background-color: #dd6b20;
    color: white;
    padding: 5px 15px;
    border-radius: 20px;
}

.risk-badge-alto {
    background-color: #e53e3e;
    color: white;
    padding: 5px 15px;
    border-radius: 20px;
}
```

## Seguridad

Protege la vista con el filtro de sesión existente:

```xml
<!-- En web.xml -->
<filter-mapping>
    <filter-name>FiltroSesion</filter-name>
    <url-pattern>/views/predicciones-ml.xhtml</url-pattern>
</filter-mapping>
```

---

**Tip**: Puedes integrar estas predicciones directamente en el dashboard del paciente para una experiencia más cohesiva.
